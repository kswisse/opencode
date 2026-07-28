import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { processNewFeedback } from "@/lib/feedback";
import { requireUser, parseBody, getPaginationParams, apiHandler } from "@/lib/api-utils";
import { createFeedbackSchema } from "@/lib/schemas";
import { logger } from "@/lib/logger";
import { checkRateLimit, getRateLimitKey } from "@/lib/rate-limit";
import { checkFeedbackLimit } from "@/lib/limits";
import { sendWebhookEvent } from "@/lib/webhooks";
import { createAuditLog } from "@/lib/audit";

export async function GET(request: Request) {
  return apiHandler(async () => {
    const { error, user } = await requireUser();
    if (error) return error;

    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get("projectId");
    const status = searchParams.get("status");
    const { page, limit, skip } = getPaginationParams(searchParams);

    const where: Record<string, unknown> = { organizationId: user.organizationId };
    if (projectId) where.projectId = projectId;
    if (status) where.status = status;

    const start = Date.now();
    const [feedback, total] = await Promise.all([
      prisma.feedback.findMany({
        where,
        orderBy: { createdAt: "desc" },
        skip,
        take: limit,
        include: {
          project: { select: { name: true, id: true } },
          author: { select: { name: true, email: true } },
          _count: { select: { votes: true, comments: true } },
        },
      }),
      prisma.feedback.count({ where }),
    ]);
    logger.api("GET", "/api/feedback", 200, Date.now() - start);

    return NextResponse.json({
      items: feedback,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    });
  }, "GET /api/feedback");
}

export async function POST(request: Request) {
  return apiHandler(async () => {
    const { error, user } = await requireUser();
    if (error) return error;

    // Rate limit: 30 feedback submissions per minute per user
    const rateLimitKey = getRateLimitKey(request, `feedback:${user.id}`);
    const rateCheck = checkRateLimit(rateLimitKey, 30, 60 * 1000);
    if (!rateCheck.allowed) {
      return NextResponse.json({
        error: "Too many requests. Please slow down.",
      }, {
        status: 429,
        headers: {
          "Retry-After": String(Math.ceil((rateCheck.resetAt - Date.now()) / 1000)),
          "X-RateLimit-Remaining": "0",
        },
      });
    }

    // Check feedback limit
    const limitCheck = await checkFeedbackLimit(user.organizationId);
    if (!limitCheck.allowed) {
      return NextResponse.json({
        error: `Monthly feedback limit reached (${limitCheck.current}/${limitCheck.limit}). Please upgrade your plan to continue.`,
        limitCheck,
      }, { status: 402 });
    }

    const parsed = await parseBody(request, createFeedbackSchema);
    if (parsed.error) return parsed.error;

    const { title, description, projectId } = parsed.data;

    const feedback = await prisma.feedback.create({
      data: {
        title,
        description: description || null,
        projectId,
        organizationId: user.organizationId,
        authorId: user.id,
      },
    });

    // Process AI features asynchronously
    processNewFeedback(feedback.id, user.organizationId).catch((err) => {
      logger.error("Failed to process new feedback AI", err instanceof Error ? err : new Error(String(err)));
    });

    // Send webhook asynchronously
    sendWebhookEvent(user.organizationId, "FEEDBACK_CREATED", {
      id: feedback.id,
      title: feedback.title,
      description: feedback.description,
      projectId: feedback.projectId,
      status: feedback.status,
      createdAt: feedback.createdAt,
    }).catch((err) => {
      logger.error("Failed to send webhook", err instanceof Error ? err : new Error(String(err)));
    });

    // Audit log
    createAuditLog({
      action: "feedback.created",
      entityType: "feedback",
      entityId: feedback.id,
      organizationId: user.organizationId,
      userId: user.id,
      userEmail: user.email,
      metadata: { title, projectId },
    }).catch(() => {});

    return NextResponse.json(feedback, { status: 201 });
  }, "POST /api/feedback");
}
