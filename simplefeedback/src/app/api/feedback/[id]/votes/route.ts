import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireUser, apiHandler } from "@/lib/api-utils";
import { notifyNewVote } from "@/lib/notifications";
import { sendWebhookEvent } from "@/lib/webhooks";
import { logger } from "@/lib/logger";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return apiHandler(async () => {
    const { id } = await params;
    const auth = await requireUser();
    if (auth.error) return auth.error;

    const existing = await prisma.feedbackVote.findUnique({
      where: { feedbackId_userId: { feedbackId: id, userId: auth.user.id } },
    });

    if (existing) {
      await prisma.feedbackVote.delete({ where: { id: existing.id } });
      const voteCount = await prisma.feedbackVote.count({ where: { feedbackId: id } });
      return NextResponse.json({ voted: false, voteCount });
    }

    await prisma.feedbackVote.create({
      data: { feedbackId: id, userId: auth.user.id },
    });

    // Create notification for the feedback author
    const fb = await prisma.feedback.findUnique({
      where: { id },
      select: { title: true, authorId: true, organizationId: true, description: true, projectId: true },
    });
    if (fb && fb.authorId !== auth.user.id) {
      notifyNewVote({
        organizationId: fb.organizationId,
        feedbackId: id,
        feedbackTitle: fb.title,
        feedbackAuthorId: fb.authorId,
      }).catch(console.error);
    }

    // Send webhook
    if (fb) {
      sendWebhookEvent(fb.organizationId, "FEEDBACK_VOTE", {
        feedbackId: id,
        feedbackTitle: fb.title,
        feedbackDescription: fb.description,
        voterId: auth.user.id,
        voterEmail: auth.user.email,
      }).catch((err) => {
        logger.error("Failed to send webhook", err instanceof Error ? err : new Error(String(err)));
      });
    }

    const voteCount = await prisma.feedbackVote.count({ where: { feedbackId: id } });
    return NextResponse.json({ voted: true, voteCount });
  }, "POST /api/feedback/[id]/votes");
}
