import React from "react";

interface WelcomeEmailProps {
  name: string;
  orgName: string;
  dashboardUrl: string;
}

export const WelcomeEmail = ({ name, orgName, dashboardUrl }: WelcomeEmailProps) => {
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://simplefeedback.com";

  return (
    <div style={{ backgroundColor: "#f6f9fc", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif", padding: "20px 0" }}>
      <div style={{ backgroundColor: "#ffffff", border: "1px solid #e6e6e6", borderRadius: "8px", margin: "0 auto", padding: "40px 20px", maxWidth: "560px" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ width: "48px", height: "48px", borderRadius: "12px", backgroundColor: "#6366f1", display: "inline-flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: "24px", fontWeight: "bold", margin: "0 auto 20px" }}>SF</div>
        </div>
        <h1 style={{ color: "#1a1a1a", fontSize: "24px", fontWeight: "700", lineHeight: "1.3", margin: "0 0 16px", textAlign: "center" }}>
          Welcome to SimpleFeedback, {name}!
        </h1>
        <p style={{ color: "#4a4a4a", fontSize: "16px", lineHeight: "1.6", margin: "0 0 16px" }}>
          Thanks for signing up! We're excited to help you collect, organize, and act on user feedback.
        </p>
        <div style={{ textAlign: "center", margin: "24px 0" }}>
          <a href={dashboardUrl} style={{ backgroundColor: "#6366f1", borderRadius: "6px", color: "#fff", display: "inline-block", fontSize: "16px", fontWeight: "600", lineHeight: "1", padding: "14px 28px", textDecoration: "none" }}>
            Go to Dashboard
          </a>
        </div>
        <p style={{ color: "#4a4a4a", fontSize: "16px", lineHeight: "1.6", margin: "0 0 16px" }}>
          Here's what you can do next:
        </p>
        <p style={{ color: "#4a4a4a", fontSize: "15px", lineHeight: "1.6", margin: "0 0 8px" }}>1. Create your first project for {orgName}</p>
        <p style={{ color: "#4a4a4a", fontSize: "15px", lineHeight: "1.6", margin: "0 0 8px" }}>2. Add the feedback widget to your website or app</p>
        <p style={{ color: "#4a4a4a", fontSize: "15px", lineHeight: "1.6", margin: "0 0 8px" }}>3. Invite your team members to collaborate</p>
        <p style={{ color: "#4a4a4a", fontSize: "15px", lineHeight: "1.6", margin: "0 0 8px" }}>4. Set up your public feedback board</p>
        <hr style={{ border: "none", borderTop: "1px solid #e6e6e6", margin: "24px 0" }} />
        <p style={{ color: "#898989", fontSize: "14px", lineHeight: "1.5", margin: "0" }}>
          If you have any questions, reply to this email or check our <a href={`${baseUrl}/docs`} style={{ color: "#6366f1", textDecoration: "underline" }}>documentation</a>.
        </p>
      </div>
    </div>
  );
};
