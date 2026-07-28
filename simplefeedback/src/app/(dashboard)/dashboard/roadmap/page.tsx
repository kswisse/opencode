import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getStatusColor, formatRelativeTime } from "@/lib/utils";
import { Target, LoaderPinwheel, CheckCircle2 } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function RoadmapPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser) redirect("/login");

  const planned = await prisma.feedback.findMany({
    where: { organizationId: dbUser.organizationId, status: "PLANNED" },
    orderBy: { aiPriorityScore: "desc" },
    include: { _count: { select: { votes: true } } },
  });

  const inProgress = await prisma.feedback.findMany({
    where: { organizationId: dbUser.organizationId, status: "IN_PROGRESS" },
    orderBy: { updatedAt: "desc" },
    include: { _count: { select: { votes: true } } },
  });

  const completed = await prisma.feedback.findMany({
    where: { organizationId: dbUser.organizationId, status: "COMPLETED" },
    orderBy: { updatedAt: "desc" },
    take: 20,
    include: { _count: { select: { votes: true } } },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Roadmap</h1>
        <p className="text-neutral-500">Drag and drop feedback to update status</p>
      </div>
      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <span className="h-2 w-2 rounded-full bg-blue-500" /> Planned ({planned.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {planned.map((item) => (
              <div key={item.id} className="rounded-lg border p-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">{item.title}</h3>
                  <span className="text-xs text-neutral-400">{item._count.votes} votes</span>
                </div>
              </div>
            ))}
            {planned.length === 0 && (
              <div className="flex flex-col items-center py-8 text-center">
                <Target className="h-8 w-8 text-neutral-300 dark:text-neutral-600" />
                <p className="mt-2 text-sm text-neutral-500">No items yet</p>
                <p className="text-xs text-neutral-400">Move feedback here when you plan to work on it</p>
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <span className="h-2 w-2 rounded-full bg-purple-500" /> In Progress ({inProgress.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {inProgress.map((item) => (
              <div key={item.id} className="rounded-lg border p-3">
                <h3 className="text-sm font-medium">{item.title}</h3>
                <p className="text-xs text-neutral-400">{item._count.votes} votes</p>
              </div>
            ))}
            {inProgress.length === 0 && (
              <div className="flex flex-col items-center py-8 text-center">
                <LoaderPinwheel className="h-8 w-8 text-neutral-300 dark:text-neutral-600" />
                <p className="mt-2 text-sm text-neutral-500">No items yet</p>
                <p className="text-xs text-neutral-400">Move feedback here when work begins</p>
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <span className="h-2 w-2 rounded-full bg-green-500" /> Completed ({completed.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {completed.map((item) => (
              <div key={item.id} className="rounded-lg border p-3 opacity-60">
                <h3 className="text-sm font-medium line-through">{item.title}</h3>
                <p className="text-xs text-neutral-400">{item._count.votes} votes</p>
              </div>
            ))}
            {completed.length === 0 && (
              <div className="flex flex-col items-center py-8 text-center">
                <CheckCircle2 className="h-8 w-8 text-neutral-300 dark:text-neutral-600" />
                <p className="mt-2 text-sm text-neutral-500">No items yet</p>
                <p className="text-xs text-neutral-400">Completed feedback will appear here</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
