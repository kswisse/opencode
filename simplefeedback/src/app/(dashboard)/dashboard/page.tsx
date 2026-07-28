import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Lightbulb, CheckCircle, Clock, TrendingUp, Plus, Users, BarChart3, Sparkles, ArrowRight } from "lucide-react";
import Link from "next/link";
import { getPlanLimit } from "@/lib/limits";
import { DashboardOnboarding } from "@/components/onboarding/dashboard-onboarding";

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: {
      organization: {
        include: { subscription: true, _count: { select: { projects: true } } },
      },
    },
  });

  if (!dbUser) redirect("/login");

  const orgId = dbUser.organizationId;
  const plan = dbUser.organization.subscription?.plan || "FREE";
  const limits = getPlanLimit(plan as keyof typeof getPlanLimit);

  const [totalFeedback, completedFeedback, openFeedback, recentFeedback, feedbackTrend, projects, recentActivity] = await Promise.all([
    prisma.feedback.count({ where: { organizationId: orgId } }),
    prisma.feedback.count({ where: { organizationId: orgId, status: "COMPLETED" } }),
    prisma.feedback.count({ where: { organizationId: orgId, status: "OPEN" } }),
    prisma.feedback.findMany({
      where: { organizationId: orgId },
      orderBy: { createdAt: "desc" },
      take: 5,
      include: {
        project: { select: { name: true, id: true } },
        author: { select: { name: true, email: true } },
      },
    }),
    // Weekly trend
    prisma.feedback.groupBy({
      by: ["createdAt"],
      where: {
        organizationId: orgId,
        createdAt: { gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) },
      },
      _count: true,
    }),
    prisma.project.findMany({
      where: { organizationId: orgId },
      select: { id: true, name: true, slug: true, _count: { select: { feedback: true } } },
      orderBy: { createdAt: "desc" },
    }),
    // Recent activity (audit logs)
    prisma.auditLog.findMany({
      where: { organizationId: orgId },
      orderBy: { createdAt: "desc" },
      take: 5,
    }),
  ]);

  // Get AI insights if available
  const aiEnabled = plan === "PRO" || plan === "BUSINESS";

  const feedbackStats = [
    { title: "Total Feedback", value: totalFeedback, icon: Lightbulb, color: "text-blue-600" },
    { title: "Open", value: openFeedback, icon: Clock, color: "text-yellow-600" },
    { title: "Completed", value: completedFeedback, icon: CheckCircle, color: "text-green-600" },
    {
      title: "Completion Rate",
      value: totalFeedback > 0 ? Math.round((completedFeedback / totalFeedback) * 100) + "%" : "0%",
      icon: TrendingUp,
      color: "text-purple-600",
    },
  ];

  // Aggregate daily counts for trend
  const dailyCounts: Record<string, number> = {};
  for (const item of feedbackTrend) {
    const day = new Date(item.createdAt).toLocaleDateString("en-US", { weekday: "short" });
    dailyCounts[day] = (dailyCounts[day] || 0) + item._count;
  }

  return (
    <div className="space-y-6">
      {/* Onboarding trigger for new users */}
      <DashboardOnboarding onboardingCompleted={dbUser.onboardingCompleted} />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-neutral-500">
            Welcome back, {dbUser.name || dbUser.email}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/dashboard/projects/new">
            <Button size="sm">
              <Plus className="h-4 w-4 mr-1" />
              New Project
            </Button>
          </Link>
          <Link href="/dashboard/settings/members">
            <Button variant="outline" size="sm">
              <Users className="h-4 w-4 mr-1" />
              Invite
            </Button>
          </Link>
        </div>
      </div>

      {/* Usage meter */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">
              Projects ({projects.length}/{limits.projects})
            </span>
            <span className="text-xs text-neutral-500">
              {limits.projects === 1 && projects.length === 0 ? "Free plan" : `${plan} plan`}
            </span>
          </div>
          <div className="w-full h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-neutral-900 dark:bg-neutral-200 rounded-full transition-all"
              style={{ width: `${Math.min((projects.length / limits.projects) * 100, 100)}%` }}
            />
          </div>
          <div className="flex items-center justify-between mt-2">
            <span className="text-sm font-medium">
              Monthly Feedback ({totalFeedback}/{limits.feedbackLimit.toLocaleString()})
            </span>
          </div>
          <div className="w-full h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden mt-1">
            <div
              className="h-full bg-neutral-900 dark:bg-neutral-200 rounded-full transition-all"
              style={{ width: `${Math.min((totalFeedback / limits.feedbackLimit) * 100, 100)}%` }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Stats grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {feedbackStats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-neutral-500">{stat.title}</CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* AI Insights */}
      {aiEnabled && (
        <Card className="border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20">
          <CardHeader className="flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-600" />
              <CardTitle>AI Insights</CardTitle>
            </div>
            <Link href="/dashboard/feedback">
              <Button variant="ghost" size="sm">
                View All <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-neutral-500">
              AI is analyzing your feedback for trends and patterns.
              {openFeedback > 0
                ? ` You have ${openFeedback} open feedback items to review.`
                : " No open feedback items to analyze."}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Feedback Trend */}
      <Card>
        <CardHeader>
          <CardTitle>This Week</CardTitle>
          <CardDescription>Daily feedback submissions</CardDescription>
        </CardHeader>
        <CardContent>
          {Object.keys(dailyCounts).length > 0 ? (
            <div className="flex items-end gap-2 h-24">
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => {
                const count = dailyCounts[day] || 0;
                const max = Math.max(...Object.values(dailyCounts), 1);
                const height = (count / max) * 100;
                return (
                  <div key={day} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-xs text-neutral-400">{count}</span>
                    <div
                      className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-t transition-all"
                      style={{ height: `${Math.max(height, 4)}%` }}
                    >
                      <div
                        className="w-full h-full bg-neutral-900 dark:bg-neutral-200 rounded-t transition-all"
                        style={{ height: `${height}%` }}
                      />
                    </div>
                    <span className="text-xs text-neutral-500">{day}</span>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-neutral-500 text-center py-8">
              No feedback this week. Share your feedback board to start collecting.
            </p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Feedback */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Feedback</CardTitle>
            <Link href="/dashboard/feedback">
              <Button variant="ghost" size="sm">
                View all <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {recentFeedback.length === 0 ? (
              <div className="text-center py-8">
                <Lightbulb className="h-8 w-8 text-neutral-300 mx-auto mb-2" />
                <p className="text-sm text-neutral-500">No feedback yet.</p>
                <Link href="/dashboard/projects">
                  <Button variant="link" size="sm">Create a project to start collecting</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {recentFeedback.map((fb) => (
                  <Link
                    key={fb.id}
                    href={`/dashboard/feedback/${fb.id}`}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-sm truncate">{fb.title}</p>
                      <p className="text-xs text-neutral-500">
                        {fb.project.name} &middot; {fb.author.name || fb.author.email}
                      </p>
                    </div>
                    <span className="text-xs text-neutral-400 shrink-0 ml-2">
                      {new Date(fb.createdAt).toLocaleDateString()}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {recentActivity.length === 0 ? (
              <div className="text-center py-8">
                <BarChart3 className="h-8 w-8 text-neutral-300 mx-auto mb-2" />
                <p className="text-sm text-neutral-500">No recent activity.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentActivity.map((log) => (
                  <div key={log.id} className="flex items-center justify-between p-2 rounded-lg">
                    <div className="min-w-0">
                      <p className="text-sm truncate">{log.action.replace(/_/g, " ")}</p>
                      <p className="text-xs text-neutral-500">
                        {log.userEmail || "System"}
                      </p>
                    </div>
                    <span className="text-xs text-neutral-400 shrink-0 ml-2">
                      {new Date(log.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-3">
            <Link href="/dashboard/projects/new">
              <Button variant="outline" className="w-full justify-start">
                <Plus className="h-4 w-4 mr-2" />
                Create Project
              </Button>
            </Link>
            <Link href="/dashboard/settings/members">
              <Button variant="outline" className="w-full justify-start">
                <Users className="h-4 w-4 mr-2" />
                Invite Member
              </Button>
            </Link>
            <Link href="/dashboard/feedback">
              <Button variant="outline" className="w-full justify-start">
                <Lightbulb className="h-4 w-4 mr-2" />
                View Feedback
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
