import { prisma } from "./prisma";
import { PLANS, type PlanType } from "./stripe";

export type LimitCheckResult = {
  allowed: boolean;
  limit: number;
  current: number;
  plan: PlanType;
};

export async function checkProjectLimit(organizationId: string): Promise<LimitCheckResult> {
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
    include: { subscription: true, _count: { select: { projects: true } } },
  });

  if (!org) throw new Error("Organization not found");

  const plan = (org.subscription?.plan || "FREE") as PlanType;
  const limit = PLANS[plan].projects;
  const current = org._count.projects;

  return {
    allowed: current < limit,
    limit,
    current,
    plan,
  };
}

export async function checkFeedbackLimit(organizationId: string): Promise<LimitCheckResult> {
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
    include: { subscription: true },
  });

  if (!org) throw new Error("Organization not found");

  const plan = (org.subscription?.plan || "FREE") as PlanType;
  const limit = PLANS[plan].feedbackLimit;

  const startOfMonth = new Date();
  startOfMonth.setDate(1);
  startOfMonth.setHours(0, 0, 0, 0);

  const current = await prisma.feedback.count({
    where: {
      organizationId,
      createdAt: { gte: startOfMonth },
    },
  });

  return {
    allowed: current < limit,
    limit,
    current,
    plan,
  };
}

export async function checkSeatLimit(organizationId: string): Promise<LimitCheckResult> {
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
    include: { subscription: true, _count: { select: { users: true } } },
  });

  if (!org) throw new Error("Organization not found");

  const plan = (org.subscription?.plan || "FREE") as PlanType;
  const limit = PLANS[plan].seats;
  const current = org._count.users;

  return {
    allowed: current < limit,
    limit,
    current,
    plan,
  };
}

export async function checkAiFeatureAccess(organizationId: string): Promise<boolean> {
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
    include: { subscription: true },
  });

  if (!org) throw new Error("Organization not found");

  const plan = (org.subscription?.plan || "FREE") as PlanType;
  return PLANS[plan].aiFeatures;
}

export function getPlanLimit(plan: PlanType): { projects: number; feedbackLimit: number; seats: number; aiFeatures: boolean } {
  return PLANS[plan];
}
