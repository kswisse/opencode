import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireUser, parseBody, getPaginationParams, apiHandler } from "@/lib/api-utils";
import { createCommentSchema } from "@/lib/schemas";
import { notifyNewComment } from "@/lib/notifications";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return apiHandler(async () => {
    const { id } = await params;
    const { page, limit, skip } = getPaginationParams(new URL(request.url).searchParams);

    const [comments, total] = await Promise.all([
      prisma.feedbackComment.findMany({
        where: { feedbackId: id },
        orderBy: { createdAt: "desc" },
        skip,
        take: limit,
        include: { user: { select: { name: true, email: true } } },
      }),
      prisma.feedbackComment.count({ where: { feedbackId: id } }),
    ]);

    return NextResponse.json({ items: comments, total, page, limit, totalPages: Math.ceil(total / limit) });
  }, "GET /api/feedback/[id]/comments");
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return apiHandler(async () => {
    const { id } = await params;
    const auth = await requireUser();
    if (auth.error) return auth.error;

    const parsed = await parseBody(request, createCommentSchema);
    if (parsed.error) return parsed.error;

    // Verify the feedback exists in this organization
    const feedback = await prisma.feedback.findFirst({
      where: { id, organizationId: auth.user.organizationId },
      select: { id: true, title: true, authorId: true, organizationId: true },
    });
    if (!feedback) {
      return NextResponse.json({ error: "Feedback not found" }, { status: 404 });
    }

    const comment = await prisma.feedbackComment.create({
      data: {
        content: parsed.data.content,
        feedbackId: id,
        userId: auth.user.id,
      },
      include: { user: { select: { name: true, email: true } } },
    });

    // Create notification for the feedback author
    notifyNewComment({
      organizationId: feedback.organizationId,
      feedbackId: id,
      feedbackTitle: feedback.title,
      commentAuthorId: auth.user.id,
      feedbackAuthorId: feedback.authorId,
    }).catch(console.error);

    return NextResponse.json(comment, { status: 201 });
  }, "POST /api/feedback/[id]/comments");
}
