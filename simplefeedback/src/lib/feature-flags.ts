import { prisma } from "./prisma";
import { PLANS, type PlanType } from "./stripe";

export type FeatureFlag =
  | "ai_features"
  | "custom_domains"
  | "api_access"
  | "sso"
  | "priority_support"
  | "advanced_analytics"
  | "team_members"
  | "webhooks"
  | "audit_logs";

const FEATURE_FLAG_PLANS: Record<FeatureFlag, PlanType[]> = {
  ai_features: ["PRO", "BUSINESS"],
  custom_domains: ["BUSINESS"],
  api_access: ["PRO", "BUSINESS"],
  sso: ["BUSINESS"],
  priority_support: ["BUSINESS"],
  advanced_analytics: ["PRO", "BUSINESS"],
  team_members: ["PRO", "BUSINESS"],
  webhooks: ["PRO", "BUSINESS"],
  audit_logs: ["BUSINESS"],
};

export function getRequiredPlan(flag: FeatureFlag): PlanType[] {
  return FEATURE_FLAG_PLANS[flag];
}

export async function hasFeature(organizationId: string, flag: FeatureFlag): Promise<boolean> {
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
    include: { subscription: true },
  });

  if (!org) return false;

  const plan = (org.subscription?.plan || "FREE") as PlanType;
  const allowedPlans = FEATURE_FLAG_PLANS[flag];
  return allowedPlans.includes(plan);
}

export async function requireFeature(organizationId: string, flag: FeatureFlag): Promise<void> {
  const allowed = await hasFeature(organizationId, flag);
  if (!allowed) {
    const plans = FEATURE_FLAG_PLANS[flag];
    throw new Error(
      `This feature requires at least ${plans.join(" or ")} plan. Please upgrade your subscription.`
    );
  }
}

export function getFeatureFlagLabel(flag: FeatureFlag): string {
  const labels: Record<FeatureFlag, string> = {
    ai_features: "AI Features",
    custom_domains: "Custom Domains",
    api_access: "API Access",
    sso: "SSO (Single Sign-On)",
    priority_support: "Priority Support",
    advanced_analytics: "Advanced Analytics",
    team_members: "Team Members",
    webhooks: "Webhooks",
    audit_logs: "Audit Logs",
  };
  return labels[flag];
}

export function getFeatureFlagDescription(flag: FeatureFlag): string {
  const descriptions: Record<FeatureFlag, string> = {
    ai_features: "AI-powered priority scoring, duplicate detection, and clustering",
    custom_domains: "Use your own domain for the feedback board",
    api_access: "REST API access with API keys",
    sso: "Single Sign-On with SAML/OIDC",
    priority_support: "Dedicated support with 4-hour response time",
    advanced_analytics: "Advanced analytics and reporting",
    team_members: "Invite team members to collaborate",
    webhooks: "Send webhook events on feedback actions",
    audit_logs: "Detailed audit logs for compliance",
  };
  return descriptions[flag];
}
