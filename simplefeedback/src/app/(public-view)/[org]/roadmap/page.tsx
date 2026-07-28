import { notFound } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getStatusColor } from "@/lib/utils";
import { Target, LoaderPinwheel, CheckCircle2 } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function PublicRoadmapPage({
  params,
}: {
  params: Promise<{ org: string }>;
}) {
  const { org: orgSlug } = await params;

  const org = await prisma.organization.findUnique({ where: { slug: orgSlug } });
  if (!org) notFound();

  const [planned, inProgress, completed] = await Promise.all([
    prisma.feedback.findMany({
      where: { organizationId: org.id, status: "PLANNED" },
      orderBy: { createdAt: "desc" },
      include: { _count: { select: { votes: true } } },
    }),
    prisma.feedback.findMany({
      where: { organizationId: org.id, status: "IN_PROGRESS" },
      orderBy: { createdAt: "desc" },
      include: { _count: { select: { votes: true } } },
    }),
    prisma.feedback.findMany({
      where: { organizationId: org.id, status: "COMPLETED" },
      orderBy: { updatedAt: "desc" },
      take: 20,
      include: { _count: { select: { votes: true } } },
    }),
  ]);

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold">{org.name} Roadmap</h1>
        <p className="mt-2 text-neutral-500">See what we&apos;re working on and what&apos;s coming next</p>
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
                <h3 className="text-sm font-medium">{item.title}</h3>
                <p className="text-xs text-neutral-400">{item._count.votes} votes</p>
              </div>
            ))}
            {planned.length === 0 && (
              <div className="flex flex-col items-center py-8 text-center">
                <Target className="h-8 w-8 text-neutral-300 dark:text-neutral-600" />
                <p className="mt-2 text-sm text-neutral-500">No items yet</p>
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
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
