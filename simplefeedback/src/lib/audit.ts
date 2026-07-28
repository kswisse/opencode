import { prisma } from "./prisma";

type AuditAction =
  | "user.invited"
  | "user.role_changed"
  | "user.removed"
  | "project.created"
  | "project.updated"
  | "project.deleted"
  | "feedback.created"
  | "feedback.status_changed"
  | "feedback.deleted"
  | "settings.updated"
  | "subscription.plan_changed"
  | "subscription.cancelled"
  | "api_key.created"
  | "api_key.deleted"
  | "webhook.created"
  | "webhook.updated"
  | "webhook.deleted"
  | "domain.updated"
  | "domain.verified"
  | "admin.impersonated"
  | "admin.plan_override"
  | "onboarding.completed";

type EntityType =
  | "user"
  | "project"
  | "feedback"
  | "organization"
  | "subscription"
  | "api_key"
  | "webhook"
  | "invite"
  | "domain";

export async function createAuditLog(params: {
  action: AuditAction;
  entityType: EntityType;
  entityId?: string;
  organizationId: string;
  userId?: string;
  userEmail?: string;
  metadata?: Record<string, unknown>;
  ipAddress?: string;
}) {
  try {
    await prisma.auditLog.create({
      data: {
        action: params.action,
        entityType: params.entityType,
        entityId: params.entityId || null,
        organizationId: params.organizationId,
        userId: params.userId || null,
        userEmail: params.userEmail || null,
        ipAddress: params.ipAddress || null,
        metadata: params.metadata ? JSON.parse(JSON.stringify(params.metadata)) : undefined,
      },
    });
  } catch (error) {
    console.error("Failed to create audit log:", error);
  }
}

export async function getAuditLogs(
  organizationId: string,
  options?: {
    limit?: number;
    offset?: number;
    action?: string;
    entityType?: string;
  }
) {
  const where: any = { organizationId };
  if (options?.action) where.action = options.action;
  if (options?.entityType) where.entityType = options.entityType;

  const [logs, total] = await Promise.all([
    prisma.auditLog.findMany({
      where,
      orderBy: { createdAt: "desc" },
      take: options?.limit || 50,
      skip: options?.offset || 0,
    }),
    prisma.auditLog.count({ where }),
  ]);

  return { logs, total };
}
