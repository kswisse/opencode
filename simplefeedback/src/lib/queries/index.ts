import { prisma } from "@/lib/prisma";

// Reusable feedback query with pagination
export async function getFeedbackList({
  organizationId,
  projectId,
  status,
  page = 1,
  limit = 20,
  includeProject = true,
  includeAuthor = true,
  includeCounts = true,
}: {
  organizationId: string;
  projectId?: string | null;
  status?: string | null;
  page?: number;
  limit?: number;
  includeProject?: boolean;
  includeAuthor?: boolean;
  includeCounts?: boolean;
}) {
  const where: Record<string, unknown> = { organizationId };
  if (projectId) where.projectId = projectId;
  if (status) where.status = status;

  const skip = (page - 1) * limit;

  const [items, total] = await Promise.all([
    prisma.feedback.findMany({
      where,
      orderBy: { createdAt: "desc" },
      skip,
      take: limit,
      include: {
        ...(includeProject ? { project: { select: { name: true, id: true } } } : {}),
        ...(includeAuthor ? { author: { select: { name: true, email: true } } } : {}),
        ...(includeCounts ? { _count: { select: { votes: true, comments: true } } } : {}),
      },
    }),
    prisma.feedback.count({ where }),
  ]);

  return { items, total, page, limit, totalPages: Math.ceil(total / limit) };
}

// Reusable changelog query with pagination
export async function getChangelogList({
  organizationId,
  publishedOnly = false,
  page = 1,
  limit = 20,
}: {
  organizationId: string;
  publishedOnly?: boolean;
  page?: number;
  limit?: number;
}) {
  const where: Record<string, unknown> = { organizationId };
  if (publishedOnly) where.publishedAt = { not: null };

  const skip = (page - 1) * limit;

  const [items, total] = await Promise.all([
    prisma.changelog.findMany({
      where,
      orderBy: publishedOnly ? { publishedAt: "desc" } : { createdAt: "desc" },
      skip,
      take: limit,
      include: { project: { select: { name: true } } },
    }),
    prisma.changelog.count({ where }),
  ]);

  return { items, total, page, limit, totalPages: Math.ceil(total / limit) };
}

// Reusable project list query
export async function getProjectList(organizationId: string) {
  return prisma.project.findMany({
    where: { organizationId },
    include: { _count: { select: { feedback: true } } },
    orderBy: { createdAt: "desc" },
  });
}

// Reusable feedback with comments query
export async function getFeedbackWithComments(feedbackId: string, organizationId: string) {
  return prisma.feedback.findFirst({
    where: { id: feedbackId, organizationId },
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
}

// Reusable roadmap data query
export async function getRoadmapData(organizationId: string) {
  const [planned, inProgress, completed] = await Promise.all([
    prisma.feedback.findMany({
      where: { organizationId, status: "PLANNED" },
      orderBy: { aiPriorityScore: "desc" },
      select: { id: true, title: true, _count: { select: { votes: true } } },
    }),
    prisma.feedback.findMany({
      where: { organizationId, status: "IN_PROGRESS" },
      orderBy: { updatedAt: "desc" },
      select: { id: true, title: true, _count: { select: { votes: true } } },
    }),
    prisma.feedback.findMany({
      where: { organizationId, status: "COMPLETED" },
      orderBy: { updatedAt: "desc" },
      take: 20,
      select: { id: true, title: true, _count: { select: { votes: true } } },
    }),
  ]);

  return { planned, inProgress, completed };
}
