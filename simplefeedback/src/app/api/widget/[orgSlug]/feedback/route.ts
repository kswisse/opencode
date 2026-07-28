import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { processNewFeedback } from "@/lib/feedback";
import { parseBody, apiHandler } from "@/lib/api-utils";
import { widgetFeedbackSchema } from "@/lib/schemas";
import { logger } from "@/lib/logger";
import { checkRateLimit, getRateLimitKey } from "@/lib/rate-limit";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: corsHeaders,
  });
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ orgSlug: string }> }
) {
  return apiHandler(async () => {
    const { orgSlug } = await params;
    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get("projectId");

    const org = await prisma.organization.findUnique({ where: { slug: orgSlug } });
    if (!org) return NextResponse.json({ error: "Not found" }, { status: 404 });

    const where: Record<string, unknown> = { organizationId: org.id, status: { not: "DECLINED" } };
    if (projectId) where.projectId = projectId;

    const feedback = await prisma.feedback.findMany({
      where,
      orderBy: [
        { aiPriorityScore: "desc" },
        { createdAt: "desc" },
      ],
      take: 100,
      include: {
        _count: { select: { votes: true, comments: true } },
      },
    });

    return NextResponse.json(feedback, { headers: corsHeaders });
  }, "GET /api/widget/[orgSlug]/feedback");
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ orgSlug: string }> }
) {
  return apiHandler(async () => {
    const { orgSlug } = await params;

    // Rate limit: 20 submissions per minute per IP for public widget
    const rateLimitKey = getRateLimitKey(request, "widget-feedback");
    const rateCheck = checkRateLimit(rateLimitKey, 20, 60 * 1000);
    if (!rateCheck.allowed) {
      return NextResponse.json({
        error: "Too many requests. Please try again later.",
      }, {
        status: 429,
        headers: {
          ...corsHeaders,
          "Retry-After": String(Math.ceil((rateCheck.resetAt - Date.now()) / 1000)),
        },
      });
    }

    const org = await prisma.organization.findUnique({
      where: { slug: orgSlug },
      include: { users: { take: 1, select: { id: true } } },
    });
    if (!org) {
      return NextResponse.json({ error: "Not found" }, { status: 404, headers: corsHeaders });
    }

    const parsed = await parseBody(request, widgetFeedbackSchema);
    if (parsed.error) return parsed.error;

    const { title, description, email, name, projectId } = parsed.data;

    let userId: string | undefined;

    if (email) {
      let user = await prisma.user.findUnique({ where: { email } });
      if (!user) {
        user = await prisma.user.create({
          data: { email, name: name || null, organizationId: org.id },
        });
      }
      userId = user.id;
    }

    const feedback = await prisma.feedback.create({
      data: {
        title,
        description: description || null,
        projectId,
        organizationId: org.id,
        authorId: userId || org.users[0]?.id,
      },
    });

    if (userId) {
      processNewFeedback(feedback.id, org.id).catch((err) => {
        logger.error("Failed to process widget feedback AI", err instanceof Error ? err : new Error(String(err)));
      });
    }

    return NextResponse.json(feedback, { status: 201, headers: corsHeaders });
  }, "POST /api/widget/[orgSlug]/feedback");
}
