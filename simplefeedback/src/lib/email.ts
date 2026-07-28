import { resend, FROM_EMAIL } from "./resend";
import { WelcomeEmail } from "@/emails/welcome";
import { FeedbackReceivedEmail } from "@/emails/feedback-received";
import { FeedbackStatusChangedEmail } from "@/emails/feedback-status-changed";
import { WeeklyDigestEmail } from "@/emails/weekly-digest";
import { InviteEmail } from "@/emails/invite";

export async function sendWelcomeEmail(
  to: string,
  name: string,
  orgName: string,
  dashboardUrl: string
) {
  return resend.emails.send({
    from: FROM_EMAIL,
    to,
    subject: `Welcome to SimpleFeedback, ${name}!`,
    react: WelcomeEmail({ name, orgName, dashboardUrl }),
  });
}

export async function sendFeedbackReceivedEmail(
  to: string,
  feedbackTitle: string,
  feedbackDescription: string | null,
  authorName: string,
  projectName: string,
  orgName: string,
  dashboardUrl: string
) {
  return resend.emails.send({
    from: FROM_EMAIL,
    to,
    subject: `New feedback: ${feedbackTitle}`,
    react: FeedbackReceivedEmail({
      feedbackTitle,
      feedbackDescription,
      authorName,
      projectName,
      orgName,
      dashboardUrl,
    }),
  });
}

export async function sendFeedbackStatusChangedEmail(
  to: string,
  feedbackTitle: string,
  oldStatus: string,
  newStatus: string,
  projectName: string,
  orgName: string,
  publicBoardUrl: string
) {
  return resend.emails.send({
    from: FROM_EMAIL,
    to,
    subject: `Feedback status updated: ${feedbackTitle}`,
    react: FeedbackStatusChangedEmail({
      feedbackTitle,
      oldStatus,
      newStatus,
      projectName,
      orgName,
      publicBoardUrl,
    }),
  });
}

export async function sendWeeklyDigestEmail(
  to: string,
  name: string,
  orgName: string,
  feedbackCount: number,
  newVotes: number,
  completedCount: number,
  topFeedbackTitle: string,
  topFeedbackVotes: number,
  dashboardUrl: string,
  weekStart: string,
  weekEnd: string
) {
  return resend.emails.send({
    from: FROM_EMAIL,
    to,
    subject: `Your ${orgName} weekly digest`,
    react: WeeklyDigestEmail({
      name,
      orgName,
      feedbackCount,
      newVotes,
      completedCount,
      topFeedbackTitle,
      topFeedbackVotes,
      dashboardUrl,
      weekStart,
      weekEnd,
    }),
  });
}

export async function sendInviteEmail(
  to: string,
  inviterName: string,
  orgName: string,
  inviteUrl: string
) {
  return resend.emails.send({
    from: FROM_EMAIL,
    to,
    subject: `${inviterName} invited you to ${orgName} on SimpleFeedback`,
    react: InviteEmail({ inviterName, orgName, inviteUrl }),
  });
}
