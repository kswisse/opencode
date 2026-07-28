import { prisma } from "./prisma";
import { detectDuplicates, scorePriority, clusterFeedback, generateReleaseNotes } from "./ai";
import { createGitHubIssue } from "./github";

export async function processNewFeedback(feedbackId: string, organizationId: string) {
  const feedback = await prisma.feedback.findUnique({
    where: { id: feedbackId },
    include: { project: true, organization: { include: { subscription: true } }, _count: { select: { votes: true } } },
  });

  if (!feedback) return;

  const hasAiFeatures = feedback.organization.subscription?.plan === "PRO" ||
    feedback.organization.subscription?.plan === "BUSINESS";

  if (!hasAiFeatures) return;

  const existingFeedback = await prisma.feedback.findMany({
    where: {
      organizationId,
      id: { not: feedbackId },
      status: { not: "DECLINED" },
    },
    select: { id: true, title: true, description: true },
  });

  const duplicateResult = await detectDuplicates(
    feedback.title,
    feedback.description,
    existingFeedback
  );

  if (duplicateResult.duplicateId) {
    await prisma.feedback.update({
      where: { id: feedbackId },
      data: { duplicateOfId: duplicateResult.duplicateId },
    });
  }

  const priorityResult = await scorePriority(
    feedback.title,
    feedback.description,
    feedback._count.votes
  );

  await prisma.feedback.update({
    where: { id: feedbackId },
    data: { aiPriorityScore: priorityResult.score },
  });
}

export async function generateAndSaveReleaseNotes(
  organizationId: string,
  projectId?: string
) {
  const completed = await prisma.feedback.findMany({
    where: {
      organizationId,
      projectId: projectId || undefined,
      status: "COMPLETED",
    },
    select: { title: true, description: true },
    take: 50,
    orderBy: { updatedAt: "desc" },
  });

  if (completed.length === 0) return null;

  const content = await generateReleaseNotes(completed);

  const changelog = await prisma.changelog.create({
    data: {
      title: `Release ${new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}`,
      content,
      organizationId,
      projectId: projectId || null,
      publishedAt: new Date(),
    },
  });

  return changelog;
}

export async function runClustering(organizationId: string) {
  const feedback = await prisma.feedback.findMany({
    where: { organizationId },
    select: { id: true, title: true, description: true },
    take: 100,
  });

  const result = await clusterFeedback(feedback);

  for (const [clusterName, ids] of Object.entries(result.clusters)) {
    await prisma.feedback.updateMany({
      where: { id: { in: ids } },
      data: { aiCluster: clusterName },
    });
  }

  return result;
}

export async function pushToGitHub(
  feedbackId: string,
  token: string,
  repo: string
) {
  const feedback = await prisma.feedback.findUnique({
    where: { id: feedbackId },
    include: { project: true },
  });

  if (!feedback || feedback.githubIssueUrl) return;

  const url = await createGitHubIssue({
    token,
    repo,
    title: feedback.title,
    body: feedback.description || "",
    labels: ["feedback", feedback.status.toLowerCase()],
  });

  await prisma.feedback.update({
    where: { id: feedbackId },
    data: { githubIssueUrl: url },
  });

  return url;
}
