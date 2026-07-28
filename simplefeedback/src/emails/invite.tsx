import React from "react";

interface InviteEmailProps {
  inviterName: string;
  orgName: string;
  inviteUrl: string;
}

export const InviteEmail = ({ inviterName, orgName, inviteUrl }: InviteEmailProps) => {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://simplefeedback.com";

  return (
    <div style={{ backgroundColor: "#f6f9fc", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif", padding: "20px 0" }}>
      <div style={{ backgroundColor: "#ffffff", border: "1px solid #e6e6e6", borderRadius: "8px", margin: "0 auto", padding: "40px 20px", maxWidth: "560px" }}>
        <h1 style={{ color: "#1a1a1a", fontSize: "28px", fontWeight: "700", lineHeight: "1.3", margin: "0 0 16px", textAlign: "center" }}>
          You're Invited!
        </h1>
        <p style={{ color: "#4a4a4a", fontSize: "16px", lineHeight: "1.6", margin: "0 0 16px" }}>
          <strong>{inviterName}</strong> has invited you to join <strong>{orgName}</strong> on SimpleFeedback.
        </p>
        <div style={{ textAlign: "center", margin: "24px 0" }}>
          <a href={inviteUrl} style={{ backgroundColor: "#6366f1", borderRadius: "6px", color: "#fff", display: "inline-block", fontSize: "16px", fontWeight: "600", lineHeight: "1", padding: "14px 28px", textDecoration: "none" }}>
            Accept Invitation
          </a>
        </div>
        <p style={{ color: "#4a4a4a", fontSize: "16px", lineHeight: "1.6", margin: "0 0 16px" }}>
          Once you join, you'll be able to:
        </p>
        <p style={{ color: "#4a4a4a", fontSize: "15px", lineHeight: "1.6", margin: "0 0 6px" }}>• Review and manage user feedback</p>
        <p style={{ color: "#4a4a4a", fontSize: "15px", lineHeight: "1.6", margin: "0 0 6px" }}>• Vote on feature requests</p>
        <p style={{ color: "#4a4a4a", fontSize: "15px", lineHeight: "1.6", margin: "0 0 6px" }}>• Collaborate on the product roadmap</p>
        <p style={{ color: "#4a4a4a", fontSize: "15px", lineHeight: "1.6", margin: "0 0 6px" }}>• Publish changelogs and updates</p>
        <hr style={{ border: "none", borderTop: "1px solid #e6e6e6", margin: "24px 0" }} />
        <p style={{ color: "#898989", fontSize: "14px", lineHeight: "1.5", margin: "0" }}>
          If you weren't expecting this invitation, you can safely ignore this email.
        </p>
      </div>
    </div>
  );
};
