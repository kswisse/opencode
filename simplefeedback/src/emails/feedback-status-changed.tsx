import React from "react";

interface FeedbackStatusChangedEmailProps {
  feedbackTitle: string;
  oldStatus: string;
  newStatus: string;
  projectName: string;
  orgName: string;
  publicBoardUrl: string;
}

const statusLabels: Record<string, string> = {
  OPEN: "Open",
  PLANNED: "Planned",
  IN_PROGRESS: "In Progress",
  COMPLETED: "Completed",
  DECLINED: "Declined",
};

const statusColors: Record<string, string> = {
  OPEN: "#f59e0b",
  PLANNED: "#3b82f6",
  IN_PROGRESS: "#8b5cf6",
  COMPLETED: "#10b981",
  DECLINED: "#6b7280",
};

export const FeedbackStatusChangedEmail = ({
  feedbackTitle,
  oldStatus,
  newStatus,
  projectName,
  orgName,
  publicBoardUrl,
}: FeedbackStatusChangedEmailProps) => {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://simplefeedback.com";
  const oldLabel = statusLabels[oldStatus] || oldStatus;
  const newLabel = statusLabels[newStatus] || newStatus;
  const newColor = statusColors[newStatus] || "#6366f1";

  return (
    <div style={{ backgroundColor: "#f6f9fc", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif", padding: "20px 0" }}>
      <div style={{ backgroundColor: "#ffffff", border: "1px solid #e6e6e6", borderRadius: "8px", margin: "0 auto", padding: "40px 20px", maxWidth: "560px" }}>
        <h1 style={{ color: "#1a1a1a", fontSize: "24px", fontWeight: "700", lineHeight: "1.3", margin: "0 0 16px" }}>
          Status Update
        </h1>
        <p style={{ color: "#4a4a4a", fontSize: "16px", lineHeight: "1.6", margin: "0 0 16px" }}>
          The status of your feedback has been updated in <strong>{projectName}</strong> ({orgName}).
        </p>
        <div style={{ backgroundColor: "#f8f9ff", border: "1px solid #e8e8ff", borderRadius: "6px", padding: "16px", margin: "16px 0" }}>
          <p style={{ color: "#1a1a1a", fontSize: "18px", fontWeight: "600", lineHeight: "1.4", margin: "0 0 12px" }}>{feedbackTitle}</p>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "8px" }}>
            <span style={{ display: "inline-block", backgroundColor: "#f3f4f6", color: "#6b7280", fontSize: "13px", fontWeight: "600", padding: "4px 12px", borderRadius: "9999px" }}>
              {oldLabel}
            </span>
            <span style={{ fontSize: "18px", color: "#9ca3af", margin: "0 4px" }}>→</span>
            <span style={{ display: "inline-block", backgroundColor: newColor, color: "#ffffff", fontSize: "13px", fontWeight: "600", padding: "4px 12px", borderRadius: "9999px" }}>
              {newLabel}
            </span>
          </div>
        </div>
        <div style={{ textAlign: "center", margin: "24px 0" }}>
          <a href={publicBoardUrl} style={{ backgroundColor: "#6366f1", borderRadius: "6px", color: "#fff", display: "inline-block", fontSize: "16px", fontWeight: "600", lineHeight: "1", padding: "14px 28px", textDecoration: "none" }}>
            View on Public Board
          </a>
        </div>
        <hr style={{ border: "none", borderTop: "1px solid #e6e6e6", margin: "24px 0" }} />
        <p style={{ color: "#898989", fontSize: "14px", lineHeight: "1.5", margin: "0" }}>
          You're receiving this because you submitted feedback for {orgName}.
        </p>
      </div>
    </div>
  );
};
