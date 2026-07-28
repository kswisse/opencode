import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin, parseBody, apiHandler } from "@/lib/api-utils";
import { widgetSettingsSchema } from "@/lib/schemas";

export async function POST(request: Request) {
  return apiHandler(async () => {
    const auth = await requireAdmin();
    if (auth.error) return auth.error;

    const parsed = await parseBody(request, widgetSettingsSchema);
    if (parsed.error) return parsed.error;

    const { projectId, buttonColor, buttonText, position, title, subtitle } = parsed.data;

    const existing = await prisma.feedbackEmbed.findFirst({
      where: { organizationId: auth.user.organizationId },
    });

    if (existing) {
      await prisma.feedbackEmbed.update({
        where: { id: existing.id },
        data: {
          projectId,
          buttonColor: buttonColor || "#6366f1",
          buttonText: buttonText || "Feedback",
          position: position || "right",
          title: title || "Share Feedback",
          subtitle: subtitle || "Help us improve",
        },
      });
    } else {
      await prisma.feedbackEmbed.create({
        data: {
          organizationId: auth.user.organizationId,
          projectId,
          buttonColor: buttonColor || "#6366f1",
          buttonText: buttonText || "Feedback",
          position: position || "right",
          title: title || "Share Feedback",
          subtitle: subtitle || "Help us improve",
        },
      });
    }

    return NextResponse.json({ success: true });
  }, "POST /api/widget-settings");
}
