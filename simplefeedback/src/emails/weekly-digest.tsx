import React from "react";

interface WeeklyDigestEmailProps {
  name: string;
  orgName: string;
  feedbackCount: number;
  newVotes: number;
  completedCount: number;
  topFeedbackTitle: string;
  topFeedbackVotes: number;
  dashboardUrl: string;
  weekStart: string;
  weekEnd: string;
}

export const WeeklyDigestEmail = ({
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
}: WeeklyDigestEmailProps) => {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://simplefeedback.com";

  return (
    <div style={{ backgroundColor: "#f6f9fc", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif", padding: "20px 0" }}>
      <div style={{ backgroundColor: "#ffffff", border: "1px solid #e6e6e6", borderRadius: "8px", margin: "0 auto", padding: "40px 20px", maxWidth: "560px" }}>
        <h1 style={{ color: "#1a1a1a", fontSize: "28px", fontWeight: "700", lineHeight: "1.3", margin: "0 0 4px", textAlign: "center" }}>
          Weekly Digest
        </h1>
        <p style={{ color: "#898989", fontSize: "14px", lineHeight: "1.5", margin: "0 0 24px", textAlign: "center" }}>
          {orgName} &middot; {weekStart} &ndash; {weekEnd}
        </p>
        <p style={{ color: "#4a4a4a", fontSize: "16px", lineHeight: "1.6", margin: "0 0 16px" }}>
          Hi {name}, here's your weekly summary:
        </p>
        <table style={{ margin: "24px 0", width: "100%", borderCollapse: "collapse" }}>
          <tr>
            <td style={{ backgroundColor: "#f8f9ff", border: "1px solid #e8e8ff", borderRadius: "8px", padding: "16px 24px", textAlign: "center", width: "33%" }}>
              <p style={{ color: "#6366f1", fontSize: "28px", fontWeight: "700", lineHeight: "1.2", margin: "0" }}>{feedbackCount}</p>
              <p style={{ color: "#6b7280", fontSize: "12px", fontWeight: "600", lineHeight: "1.4", margin: "4px 0 0", textTransform: "uppercase" }}>New Feedback</p>
            </td>
            <td style={{ backgroundColor: "#f8f9ff", border: "1px solid #e8e8ff", borderRadius: "8px", padding: "16px 24px", textAlign: "center", width: "33%" }}>
              <p style={{ color: "#6366f1", fontSize: "28px", fontWeight: "700", lineHeight: "1.2", margin: "0" }}>{newVotes}</p>
              <p style={{ color: "#6b7280", fontSize: "12px", fontWeight: "600", lineHeight: "1.4", margin: "4px 0 0", textTransform: "uppercase" }}>New Votes</p>
            </td>
            <td style={{ backgroundColor: "#f8f9ff", border: "1px solid #e8e8ff", borderRadius: "8px", padding: "16px 24px", textAlign: "center", width: "33%" }}>
              <p style={{ color: "#6366f1", fontSize: "28px", fontWeight: "700", lineHeight: "1.2", margin: "0" }}>{completedCount}</p>
              <p style={{ color: "#6b7280", fontSize: "12px", fontWeight: "600", lineHeight: "1.4", margin: "4px 0 0", textTransform: "uppercase" }}>Completed</p>
            </td>
          </tr>
        </table>
        {topFeedbackTitle && (
          <div style={{ backgroundColor: "#fffbeb", border: "1px solid #fde68a", borderRadius: "6px", padding: "16px", margin: "16px 0" }}>
            <p style={{ color: "#92400e", fontSize: "12px", fontWeight: "600", margin: "0 0 8px", textTransform: "uppercase" }}>Top Feedback This Week</p>
            <p style={{ color: "#1a1a1a", fontSize: "16px", fontWeight: "600", lineHeight: "1.4", margin: "0 0 4px" }}>{topFeedbackTitle}</p>
            <p style={{ color: "#92400e", fontSize: "14px", fontWeight: "500", margin: "0" }}>{topFeedbackVotes} votes</p>
          </div>
        )}
        <div style={{ textAlign: "center", margin: "24px 0" }}>
          <a href={dashboardUrl} style={{ backgroundColor: "#6366f1", borderRadius: "6px", color: "#fff", display: "inline-block", fontSize: "16px", fontWeight: "600", lineHeight: "1", padding: "14px 28px", textDecoration: "none" }}>
            View Full Dashboard
          </a>
        </div>
        <hr style={{ border: "none", borderTop: "1px solid #e6e6e6", margin: "24px 0" }} />
        <p style={{ color: "#898989", fontSize: "14px", lineHeight: "1.5", margin: "0" }}>
          <a href={`${baseUrl}/settings/notifications`} style={{ color: "#6366f1", textDecoration: "underline" }}>Manage digest preferences</a>
        </p>
      </div>
    </div>
  );
};
