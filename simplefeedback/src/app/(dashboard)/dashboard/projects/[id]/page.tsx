import { notFound, redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getStatusColor, formatRelativeTime } from "@/lib/utils";
import { ArrowUp, Lightbulb } from "lucide-react";

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser) redirect("/login");

  const project = await prisma.project.findFirst({
    where: { id, organizationId: dbUser.organizationId },
    include: {
      feedback: {
        orderBy: { createdAt: "desc" },
        include: {
          _count: { select: { votes: true, comments: true } },
          author: { select: { name: true, email: true } },
        },
      },
    },
  });

  if (!project) notFound();

  const statusCounts = {
    OPEN: project.feedback.filter((f) => f.status === "OPEN").length,
    PLANNED: project.feedback.filter((f) => f.status === "PLANNED").length,
    IN_PROGRESS: project.feedback.filter((f) => f.status === "IN_PROGRESS").length,
    COMPLETED: project.feedback.filter((f) => f.status === "COMPLETED").length,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{project.name}</h1>
        {project.description && <p className="text-neutral-500">{project.description}</p>}
      </div>
      <div className="grid grid-cols-4 gap-4">
        {Object.entries(statusCounts).map(([status, count]) => (
          <Card key={status}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-neutral-500">{status.replace("_", " ")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{count}</div>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Feedback</CardTitle>
        </CardHeader>
        <CardContent>
            {project.feedback.length === 0 ? (
            <div className="flex flex-col items-center py-12 text-center">
              <div className="rounded-full bg-neutral-100 p-3 dark:bg-neutral-800">
                <Lightbulb className="h-6 w-6 text-neutral-400" />
              </div>
              <p className="mt-4 text-sm font-medium text-neutral-700 dark:text-neutral-300">No feedback yet</p>
              <p className="mt-1 text-xs text-neutral-500">Share your public board to start collecting feedback.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {project.feedback.map((fb) => (
                <div key={fb.id} className="flex items-start gap-4 rounded-lg border p-4">
                  <div className="flex flex-col items-center gap-1 pt-1">
                    <ArrowUp className="h-4 w-4 text-neutral-400" />
                    <span className="text-sm font-medium">{fb._count.votes}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{fb.title}</h3>
                      <Badge className={getStatusColor(fb.status)} variant="secondary">
                        {fb.status.replace("_", " ")}
                      </Badge>
                    </div>
                    {fb.description && (
                      <p className="mt-1 text-sm text-neutral-500 line-clamp-2">{fb.description}</p>
                    )}
                    <div className="mt-2 flex items-center gap-3 text-xs text-neutral-400">
                      <span>{fb.author.name || fb.author.email}</span>
                      <span>{formatRelativeTime(fb.createdAt)}</span>
                      <span>{fb._count.comments} comments</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
