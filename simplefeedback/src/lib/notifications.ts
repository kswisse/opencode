import { prisma } from "@/lib/prisma";

type NotificationType = "STATUS_CHANGE" | "NEW_COMMENT" | "NEW_VOTE";

export async function createNotification(params: {
  organizationId: string;
  userId: string;
  type: NotificationType;
  title: string;
  message: string;
  link?: string;
  feedbackId?: string;
}) {
  const notification = await prisma.notification.create({
    data: {
      organizationId: params.organizationId,
      userId: params.userId,
      type: params.type,
      title: params.title,
      message: params.message,
      link: params.link || null,
      feedbackId: params.feedbackId || null,
    },
  });
  return notification;
}

export async function notifyFeedbackStatusChange(params: {
  organizationId: string;
  feedbackId: string;
  feedbackTitle: string;
  newStatus: string;
  authorId: string;
}) {
  return createNotification({
    organizationId: params.organizationId,
    userId: params.authorId,
    type: "STATUS_CHANGE",
    title: "Feedback status updated",
    message: `"${params.feedbackTitle}" is now ${params.newStatus.replace("_", " ").toLowerCase()}`,
    link: `/dashboard/feedback/${params.feedbackId}`,
    feedbackId: params.feedbackId,
  });
}

export async function notifyNewComment(params: {
  organizationId: string;
  feedbackId: string;
  feedbackTitle: string;
  commentAuthorId: string;
  feedbackAuthorId: string;
}) {
  // Don't notify if commenting on your own feedback
  if (params.commentAuthorId === params.feedbackAuthorId) return;

  return createNotification({
    organizationId: params.organizationId,
    userId: params.feedbackAuthorId,
    type: "NEW_COMMENT",
    title: "New comment on your feedback",
    message: `Someone commented on "${params.feedbackTitle}"`,
    link: `/dashboard/feedback/${params.feedbackId}`,
    feedbackId: params.feedbackId,
  });
}

export async function notifyNewVote(params: {
  organizationId: string;
  feedbackId: string;
  feedbackTitle: string;
  feedbackAuthorId: string;
}) {
  return createNotification({
    organizationId: params.organizationId,
    userId: params.feedbackAuthorId,
    type: "NEW_VOTE",
    title: "New vote on your feedback",
    message: `"${params.feedbackTitle}" received a new vote`,
    link: `/dashboard/feedback/${params.feedbackId}`,
    feedbackId: params.feedbackId,
  });
}
