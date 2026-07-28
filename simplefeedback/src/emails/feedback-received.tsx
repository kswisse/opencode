import React from "react";

interface FeedbackReceivedEmailProps {
  feedbackTitle: string;
  feedbackDescription: string | null;
  authorName: string;
  projectName: string;
  orgName: string;
  dashboardUrl: string;
}

export const FeedbackReceivedEmail = ({
  feedbackTitle,
  feedbackDescription,
  authorName,
  projectName,
  orgName,
  dashboardUrl,
}: FeedbackReceivedEmailProps) => {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://simplefeedback.com";

  return (
    <div style={{ backgroundColor: "#f6f9fc", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif", padding: "20px 0" }}>
      <div style={{ backgroundColor: "#ffffff", border: "1px solid #e6e6e6", borderRadius: "8px", margin: "0 auto", padding: "40px 20px", maxWidth: "560px" }}>
        <h1 style={{ color: "#1a1a1a", fontSize: "24px", fontWeight: "700", lineHeight: "1.3", margin: "0 0 16px" }}>
          New Feedback Submitted
        </h1>
        <p style={{ color: "#4a4a4a", fontSize: "16px", lineHeight: "1.6", margin: "0 0 16px" }}>
          <strong>{authorName}</strong> has submitted new feedback in <strong>{projectName}</strong> ({orgName}).
        </p>
        <div style={{ backgroundColor: "#f8f9ff", border: "1px solid #e8e8ff", borderRadius: "6px", padding: "16px", margin: "16px 0" }}>
          <p style={{ color: "#1a1a1a", fontSize: "18px", fontWeight: "600", lineHeight: "1.4", margin: "0 0 8px" }}>{feedbackTitle}</p>
          {feedbackDescription && (
            <p style={{ color: "#4a4a4a", fontSize: "14px", lineHeight: "1.6", margin: "0" }}>{feedbackDescription}</p>
          )}
        </div>
        <div style={{ textAlign: "center", margin: "24px 0" }}>
          <a href={dashboardUrl} style={{ backgroundColor: "#6366f1", borderRadius: "6px", color: "#fff", display: "inline-block", fontSize: "16px", fontWeight: "600", lineHeight: "1", padding: "14px 28px", textDecoration: "none" }}>
            View in Dashboard
          </a>
        </div>
        <hr style={{ border: "none", borderTop: "1px solid #e6e6e6", margin: "24px 0" }} />
        <p style={{ color: "#898989", fontSize: "14px", lineHeight: "1.5", margin: "0" }}>
          <a href={`${baseUrl}/settings/notifications`} style={{ color: "#6366f1", textDecoration: "underline" }}>Manage your notification preferences</a>
        </p>
      </div>
    </div>
  );
};
