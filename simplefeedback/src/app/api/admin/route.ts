import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { createClient } from "@/lib/supabase-server";

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser || dbUser.role !== "SUPER_ADMIN") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const [
    totalOrganizations,
    totalUsers,
    totalFeedback,
    planDistribution,
    recentOrganizations,
    monthlyFeedback,
  ] = await Promise.all([
    prisma.organization.count(),
    prisma.user.count(),
    prisma.feedback.count(),
    prisma.subscription.groupBy({
      by: ["plan"],
      _count: true,
    }),
    prisma.organization.findMany({
      orderBy: { createdAt: "desc" },
      take: 20,
      include: {
        _count: { select: { users: true, feedback: true, projects: true } },
        subscription: { select: { plan: true, status: true } },
      },
    }),
    prisma.feedback.count({
      where: {
        createdAt: { gte: new Date(new Date().setDate(new Date().getDate() - 30)) },
      },
    }),
  ]);

  return NextResponse.json({
    stats: {
      totalOrganizations,
      totalUsers,
      totalFeedback,
      monthlyFeedback,
      planDistribution,
    },
    organizations: recentOrganizations,
  });
}

export async function PUT(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser || dbUser.role !== "SUPER_ADMIN") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const body = await request.json();
  const { action, organizationId, plan } = body;

  if (action === "override_plan") {
    if (!organizationId || !plan) {
      return NextResponse.json({ error: "organizationId and plan are required" }, { status: 400 });
    }

    const subscription = await prisma.subscription.upsert({
      where: { organizationId },
      create: { organizationId, plan },
      update: { plan },
    });

    return NextResponse.json({ success: true, subscription });
  }

  return NextResponse.json({ error: "Unknown action" }, { status: 400 });
}
