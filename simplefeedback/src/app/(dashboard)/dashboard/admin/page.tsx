import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AdminClient } from "./admin-client";

export default async function AdminPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser || dbUser.role !== "SUPER_ADMIN") {
    redirect("/dashboard");
  }

  const [
    totalOrganizations,
    totalUsers,
    totalFeedback,
    planDistribution,
    recentOrganizations,
    feedback30d,
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
        createdAt: { gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
      },
    }),
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Admin Panel</h1>
        <p className="text-neutral-500">
          System-wide management and monitoring
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-500">Organizations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalOrganizations}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-500">Total Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalUsers}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-500">Total Feedback</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFeedback}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-500">Feedback (30d)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{feedback30d}</div>
          </CardContent>
        </Card>
      </div>

      {/* Plan Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Plan Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            {["FREE", "PRO", "BUSINESS"].map((plan) => {
              const count = planDistribution.find((p) => p.plan === plan)?._count || 0;
              const total = planDistribution.reduce((a, b) => a + b._count, 0);
              const pct = total > 0 ? Math.round((count / total) * 100) : 0;
              return (
                <div key={plan} className="flex-1 text-center p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-lg">
                  <div className="text-2xl font-bold">{count}</div>
                  <div className="text-xs text-neutral-500 mt-1">{plan}</div>
                  <div className="text-xs text-neutral-400">{pct}%</div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Organizations List */}
      <Card>
        <CardHeader>
          <CardTitle>Organizations</CardTitle>
          <CardDescription>Recent organizations (last 20)</CardDescription>
        </CardHeader>
        <CardContent>
          <AdminClient organizations={recentOrganizations} />
        </CardContent>
      </Card>
    </div>
  );
}
