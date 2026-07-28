import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

// Safely encode a string value for embedding into a JavaScript string literal
// Uses JSON.stringify which handles all special characters (quotes, backslashes, newlines, etc.)
function safeJs(value: unknown): string {
  return JSON.stringify(value ?? "");
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ orgSlug: string }> }
) {
  const { orgSlug } = await params;

  const org = await prisma.organization.findUnique({
    where: { slug: orgSlug },
    include: {
      feedbackEmbeds: { take: 1 },
      projects: { take: 1 },
    },
  });

  if (!org) return NextResponse.json({ error: "Not found" }, { status: 404 });

  const embed = org.feedbackEmbeds[0];
  const project = org.projects[0];

  // All user-controlled values are safely encoded via safeJs() to prevent XSS
  // JSON.stringify escapes quotes, backslashes, newlines, and other JS special chars
  const safeOrgSlug = safeJs(orgSlug);
  const safeProjectId = safeJs(embed?.projectId || project?.id || "");
  const safeButtonColor = safeJs(embed?.buttonColor || "#6366f1");
  const safeButtonText = safeJs(embed?.buttonText || "Feedback");
  const safePosition = safeJs(embed?.position || "right");
  const safeWidgetTitle = safeJs(embed?.title || "Share Feedback");
  const safeWidgetSubtitle = safeJs(embed?.subtitle || "Help us improve");
  const safeAppUrl = safeJs(process.env.NEXT_PUBLIC_APP_URL || "");
  const safeButtonTextDisplay = safeJs(embed?.buttonText || "Feedback");

  const script = `
(function() {
  var config = {
    orgSlug: ${safeOrgSlug},
    projectId: ${safeProjectId},
    buttonColor: ${safeButtonColor},
    buttonText: ${safeButtonText},
    position: ${safePosition},
    widgetTitle: ${safeWidgetTitle},
    widgetSubtitle: ${safeWidgetSubtitle},
    appUrl: ${safeAppUrl}
  };

  // Create button - use textContent to prevent HTML injection
  var btn = document.createElement("button");
  btn.textContent = config.buttonText;
  btn.style.cssText = "position:fixed;bottom:20px;" + config.position + ":20px;z-index:99999;background:" + config.buttonColor + ";color:white;border:none;border-radius:8px;padding:12px 20px;font-size:14px;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.15);transition:all 0.2s;font-family:-apple-system,BlinkMacSystemFont,\\"Segoe UI\\",Roboto,sans-serif;";
  btn.onmouseover = function() { this.style.opacity = "0.9"; };
  btn.onmouseout = function() { this.style.opacity = "1"; };
  document.body.appendChild(btn);

  // Create modal container
  var modal = document.createElement("div");
  modal.style.cssText = "display:none;position:fixed;top:0;left:0;right:0;bottom:0;z-index:99999;background:rgba(0,0,0,0.5);justify-content:center;align-items:center;";

  // Build modal content safely - use textContent for user-controlled text
  var modalContent = document.createElement("div");
  modalContent.style.cssText = "background:white;border-radius:12px;padding:24px;width:100%;max-width:440px;margin:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);font-family:-apple-system,BlinkMacSystemFont,\\"Segoe UI\\",Roboto,sans-serif;box-sizing:border-box;";

  // Header with title and close button
  var header = document.createElement("div");
  header.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;";
  var titleEl = document.createElement("h2");
  titleEl.style.cssText = "font-size:18px;margin:0;color:#111;";
  titleEl.textContent = config.widgetTitle;
  header.appendChild(titleEl);
  var closeBtn = document.createElement("button");
  closeBtn.id = "sf-close";
  closeBtn.textContent = "\\u00D7";
  closeBtn.style.cssText = "background:none;border:none;font-size:24px;cursor:pointer;color:#666;line-height:1;padding:0;";
  closeBtn.setAttribute("aria-label", "Close");
  header.appendChild(closeBtn);
  modalContent.appendChild(header);

  // Subtitle
  var subtitleEl = document.createElement("p");
  subtitleEl.style.cssText = "font-size:14px;color:#666;margin-bottom:16px;";
  subtitleEl.textContent = config.widgetSubtitle;
  modalContent.appendChild(subtitleEl);

  // Email input
  var emailInput = document.createElement("input");
  emailInput.id = "sf-email";
  emailInput.type = "email";
  emailInput.placeholder = "Your email (optional)";
  emailInput.style.cssText = "width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px;margin-bottom:12px;box-sizing:border-box;";
  modalContent.appendChild(emailInput);

  // Name input
  var nameInput = document.createElement("input");
  nameInput.id = "sf-name";
  nameInput.type = "text";
  nameInput.placeholder = "Your name (optional)";
  nameInput.style.cssText = "width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px;margin-bottom:12px;box-sizing:border-box;";
  modalContent.appendChild(nameInput);

  // Title input
  var titleInput = document.createElement("input");
  titleInput.id = "sf-title";
  titleInput.type = "text";
  titleInput.placeholder = "Summary of your feedback";
  titleInput.style.cssText = "width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px;margin-bottom:12px;box-sizing:border-box;";
  modalContent.appendChild(titleInput);

  // Description textarea
  var descInput = document.createElement("textarea");
  descInput.id = "sf-description";
  descInput.placeholder = "Tell us more (optional)";
  descInput.rows = 4;
  descInput.style.cssText = "width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px;margin-bottom:16px;resize:vertical;box-sizing:border-box;font-family:inherit;";
  modalContent.appendChild(descInput);

  // Submit button
  var submitBtn = document.createElement("button");
  submitBtn.id = "sf-submit";
  submitBtn.textContent = "Submit Feedback";
  submitBtn.style.cssText = "width:100%;padding:12px;background:" + config.buttonColor + ";color:white;border:none;border-radius:8px;font-size:15px;font-weight:500;cursor:pointer;";
  modalContent.appendChild(submitBtn);

  // Message area
  var messageEl = document.createElement("p");
  messageEl.id = "sf-message";
  messageEl.style.cssText = "font-size:13px;margin-top:8px;display:none;";
  modalContent.appendChild(messageEl);

  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  // Event handlers
  btn.onclick = function() { modal.style.display = "flex"; };
  document.getElementById("sf-close").onclick = function() { modal.style.display = "none"; };
  modal.onclick = function(e) { if (e.target === modal) modal.style.display = "none"; };

  document.getElementById("sf-submit").onclick = function() {
    var titleVal = document.getElementById("sf-title").value;
    if (!titleVal) { alert("Please enter a title"); return; }
    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting...";
    fetch(config.appUrl + "/api/widget/" + config.orgSlug + "/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: titleVal,
        description: document.getElementById("sf-description").value,
        email: document.getElementById("sf-email").value || undefined,
        name: document.getElementById("sf-name").value || undefined,
        projectId: config.projectId
      })
    }).then(function(r) { return r.json(); }).then(function() {
      messageEl.style.display = "block";
      messageEl.style.color = "green";
      messageEl.textContent = "Thank you for your feedback!";
      document.getElementById("sf-title").value = "";
      document.getElementById("sf-description").value = "";
      document.getElementById("sf-email").value = "";
      document.getElementById("sf-name").value = "";
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Feedback";
      setTimeout(function() { modal.style.display = "none"; messageEl.style.display = "none"; }, 2000);
    }).catch(function() {
      messageEl.style.display = "block";
      messageEl.style.color = "red";
      messageEl.textContent = "Something went wrong. Please try again.";
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Feedback";
    });
  };
})();
`;

  return new NextResponse(script, {
    headers: {
      "Content-Type": "application/javascript; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
