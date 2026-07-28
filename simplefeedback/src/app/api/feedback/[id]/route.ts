import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireUser, requireAdmin, parseBody, apiHandler } from "@/lib/api-utils";
import { updateFeedbackSchema } from "@/lib/schemas";
import { logger } from "@/lib/logger";
import { notifyFeedbackStatusChange } from "@/lib/notifications";
import { sendWebhookEvent } from "@/lib/webhooks";
import { createAuditLog } from "@/lib/audit";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return apiHandler(async () => {
    const { id } = await params;
    const auth = await requireUser();
    if (auth.error) return auth.error;

    const feedback = await prisma.feedback.findFirst({
      where: { id, organizationId: auth.user.organizationId },
      include: {
        project: { select: { name: true } },
        author: { select: { name: true, email: true } },
        _count: { select: { votes: true, comments: true } },
        comments: {
          orderBy: { createdAt: "desc" },
          include: { user: { select: { name: true, email: true } } },
        },
        duplicateOf: { select: { id: true, title: true } },
      },
    });

    if (!feedback) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    return NextResponse.json(feedback);
  }, "GET /api/feedback/[id]");
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return apiHandler(async () => {
    const { id } = await params;
    const auth = await requireAdmin();
    if (auth.error) return auth.error;

    const parsed = await parseBody(request, updateFeedbackSchema);
    if (parsed.error) return parsed.error;

    const { status, priority } = parsed.data;

    // Fetch current feedback to check for status change
    const currentFeedback = status ? await prisma.feedback.findFirst({
      where: { id, organizationId: auth.user.organizationId },
      select: { title: true, status: true, authorId: true, organizationId: true, description: true, projectId: true },
    }) : null;

    const result = await prisma.feedback.updateMany({
      where: { id, organizationId: auth.user.organizationId },
      data: {
        ...(status && { status }),
        ...(priority && { priority }),
      },
    });

    if (result.count === 0) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    // Create notification for status change
    if (status && currentFeedback && status !== currentFeedback.status) {
      notifyFeedbackStatusChange({
        organizationId: currentFeedback.organizationId,
        feedbackId: id,
        feedbackTitle: currentFeedback.title,
        newStatus: status,
        authorId: currentFeedback.authorId,
      }).catch(console.error);

      // Send webhook
      sendWebhookEvent(currentFeedback.organizationId, "FEEDBACK_STATUS_CHANGED", {
        id,
        title: currentFeedback.title,
        description: currentFeedback.description,
        projectId: currentFeedback.projectId,
        oldStatus: currentFeedback.status,
        newStatus: status,
      }).catch((err) => {
        logger.error("Failed to send webhook", err instanceof Error ? err : new Error(String(err)));
      });

      // Audit log
      createAuditLog({
        action: "feedback.status_changed",
        entityType: "feedback",
        entityId: id,
        organizationId: currentFeedback.organizationId,
        userId: auth.user.id,
        userEmail: auth.user.email,
        metadata: { oldStatus: currentFeedback.status, newStatus: status },
      }).catch(() => {});
    }

    return NextResponse.json({ success: true });
  }, "PATCH /api/feedback/[id]");
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return apiHandler(async () => {
    const { id } = await params;
    const auth = await requireAdmin();
    if (auth.error) return auth.error;

    const result = await prisma.feedback.deleteMany({
      where: { id, organizationId: auth.user.organizationId },
    });

    if (result.count === 0) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    return new NextResponse(null, { status: 204 });
  }, "DELETE /api/feedback/[id]");
}
