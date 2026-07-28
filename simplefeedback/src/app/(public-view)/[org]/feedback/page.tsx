import { notFound } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { PublicFeedbackBoard } from "@/components/feedback/public-feedback-board";

export const dynamic = "force-dynamic";

export default async function PublicFeedbackPage({
  params,
}: {
  params: Promise<{ org: string }>;
}) {
  const { org: orgSlug } = await params;

  const org = await prisma.organization.findUnique({
    where: { slug: orgSlug },
    include: {
      projects: { select: { id: true, name: true } },
    },
  });

  if (!org) notFound();

  const feedback = await prisma.feedback.findMany({
    where: { organizationId: org.id, status: { not: "DECLINED" } },
    orderBy: [{ aiPriorityScore: "desc" }, { createdAt: "desc" }],
    include: {
      project: { select: { name: true } },
      _count: { select: { votes: true, comments: true } },
    },
  });

  return (
    <PublicFeedbackBoard
      orgSlug={orgSlug}
      orgName={org.name}
      projects={org.projects}
      feedback={feedback.map((f) => ({
        id: f.id,
        title: f.title,
        description: f.description,
        status: f.status,
        createdAt: f.createdAt.toISOString(),
        projectName: f.project.name,
        voteCount: f._count.votes,
        commentCount: f._count.comments,
      }))}
    />
  );
}
