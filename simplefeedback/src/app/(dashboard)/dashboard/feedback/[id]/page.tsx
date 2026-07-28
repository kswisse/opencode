import { notFound, redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getStatusColor, formatDate } from "@/lib/utils";
import { ArrowUp, MessageSquare, ExternalLink } from "lucide-react";
import Link from "next/link";
import { FeedbackStatusActions } from "@/components/feedback/feedback-status-actions";
import { FeedbackComments } from "@/components/feedback/feedback-comments";

export default async function FeedbackDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser || dbUser.role !== "ADMIN") redirect("/login");

  const feedback = await prisma.feedback.findFirst({
    where: { id, organizationId: dbUser.organizationId },
    include: {
      project: { select: { name: true } },
      author: { select: { name: true, email: true } },
      _count: { select: { votes: true, comments: true } },
      comments: {
        orderBy: { createdAt: "desc" },
        include: { user: { select: { name: true, email: true } } },
      },
      duplicateOf: { select: { id: true, title: true } },
    },
  });

  if (!feedback) notFound();

  return (
    <div className="space-y-6">
      <div>
        <Link href="/dashboard/feedback" className="text-sm text-neutral-500 hover:text-neutral-900">
          &larr; Back to Feedback
        </Link>
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold">{feedback.title}</h1>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge className={getStatusColor(feedback.status)} variant="secondary">
                  {feedback.status.replace("_", " ")}
                </Badge>
                <span className="text-sm text-neutral-400">{feedback.project.name}</span>
                <span className="text-sm text-neutral-400">{formatDate(feedback.createdAt)}</span>
              </div>
            </CardHeader>
            <CardContent>
              {feedback.description && (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p>{feedback.description}</p>
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Comments ({feedback._count.comments})</CardTitle>
            </CardHeader>
            <CardContent>
              <FeedbackComments
                feedbackId={feedback.id}
                comments={feedback.comments.map((c) => ({
                  id: c.id,
                  content: c.content,
                  createdAt: c.createdAt,
                  author: { name: c.user.name, email: c.user.email },
                }))}
              />
            </CardContent>
          </Card>
        </div>
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <FeedbackStatusActions feedbackId={feedback.id} currentStatus={feedback.status} />
              <div className="flex items-center gap-4 text-sm text-neutral-500">
                <span className="flex items-center gap-1">
                  <ArrowUp className="h-4 w-4" /> {feedback._count.votes} votes
                </span>
                <span className="flex items-center gap-1">
                  <MessageSquare className="h-4 w-4" /> {feedback._count.comments} comments
                </span>
              </div>
              {feedback.aiPriorityScore && (
                <div>
                  <p className="text-sm font-medium">AI Priority Score</p>
                  <div className="mt-1 h-2 w-full rounded-full bg-neutral-200">
                    <div
                      className="h-2 rounded-full bg-indigo-500"
                      style={{ width: `${feedback.aiPriorityScore}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-neutral-500">{Math.round(feedback.aiPriorityScore)}/100</p>
                </div>
              )}
              {feedback.duplicateOf && (
                <div>
                  <p className="text-sm font-medium">Duplicate of</p>
                  <Link
                    href={`/dashboard/feedback/${feedback.duplicateOf.id}`}
                    className="text-sm text-indigo-600 hover:underline"
                  >
                    {feedback.duplicateOf.title}
                  </Link>
                </div>
              )}
              {feedback.githubIssueUrl && (
                <Button variant="outline" size="sm" asChild className="w-full">
                  <a href={feedback.githubIssueUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="mr-2 h-4 w-4" /> View on GitHub
                  </a>
                </Button>
              )}
              <div className="text-xs text-neutral-400">
                Submitted by {feedback.author.name || feedback.author.email}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
