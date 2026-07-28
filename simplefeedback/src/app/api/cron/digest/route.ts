import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { sendWeeklyDigestEmail } from "@/lib/email";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * Weekly digest cron endpoint.
 * This should be called by a cron job (e.g., Vercel Cron Jobs) every Monday at 9 AM.
 *
 * CRON_SECRET must match to prevent unauthorized access.
 */
export async function GET(request: Request) {
  try {
    // Verify cron secret
    const authHeader = request.headers.get("authorization");
    const expected = `Bearer ${process.env.CRON_SECRET}`;

    if (!authHeader || authHeader !== expected) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    // Get all organizations with admin users
    const organizations = await prisma.organization.findMany({
      include: {
        users: {
          where: { role: "ADMIN" },
        },
      },
    });

    const weekStart = weekAgo.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
    const weekEnd = now.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });

    let sentCount = 0;

    for (const org of organizations) {
      // Get weekly stats
      const feedbackCount = await prisma.feedback.count({
        where: {
          organizationId: org.id,
          createdAt: { gte: weekAgo },
        },
      });

      const newVotes = await prisma.feedbackVote.count({
        where: {
          feedback: { organizationId: org.id },
          createdAt: { gte: weekAgo },
        },
      });

      const completedCount = await prisma.feedback.count({
        where: {
          organizationId: org.id,
          status: "COMPLETED",
          updatedAt: { gte: weekAgo },
        },
      });

      // Get top feedback
      const topFeedback = await prisma.feedback.findFirst({
        where: { organizationId: org.id },
        orderBy: {
          votes: { _count: "desc" },
        },
        include: { _count: { select: { votes: true } } },
      });

      // Send digest to each admin
      for (const user of org.users) {
        if (!user.email || !user.name) continue;

        try {
          await sendWeeklyDigestEmail(
            user.email,
            user.name,
            org.name,
            feedbackCount,
            newVotes,
            completedCount,
            topFeedback?.title || "No feedback this week",
            topFeedback?._count.votes || 0,
            `${process.env.NEXT_PUBLIC_APP_URL}/dashboard`,
            weekStart,
            weekEnd
          );
          sentCount++;
        } catch (emailError) {
          console.error(
            `Failed to send digest to ${user.email}:`,
            emailError
          );
        }
      }
    }

    return NextResponse.json({
      success: true,
      organizations: organizations.length,
      emailsSent: sentCount,
    });
  } catch (error) {
    console.error("Digest cron error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
