import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireUser, requireAdmin, parseBody, apiHandler } from "@/lib/api-utils";
import { updateOrganizationNameSchema } from "@/lib/schemas";
import { PLANS, type PlanType } from "@/lib/stripe";

export async function GET() {
  return apiHandler(async () => {
    const auth = await requireUser(true);
    if (auth.error) return auth.error;

    const org = auth.user.organization;
    const plan = (org.subscription?.plan || "FREE") as PlanType;
    const limits = PLANS[plan];

    return NextResponse.json({
      id: org.id,
      name: org.name,
      slug: org.slug,
      customDomain: org.customDomain,
      domainVerified: org.domainVerified,
      plan: org.subscription?.plan || "FREE",
      projectsCount: org._count?.projects || 0,
      feedbackCount: org._count?.feedback || 0,
      limits: {
        projects: limits.projects,
        feedbackLimit: limits.feedbackLimit,
        seats: limits.seats,
        aiFeatures: limits.aiFeatures,
      },
    });
  }, "GET /api/organization");
}

export async function PATCH(request: Request) {
  return apiHandler(async () => {
    const auth = await requireAdmin();
    if (auth.error) return auth.error;

    const parsed = await parseBody(request, updateOrganizationNameSchema);
    if (parsed.error) return parsed.error;

    const { name } = parsed.data;

    await prisma.organization.update({
      where: { id: auth.user.organizationId },
      data: { name },
    });

    return NextResponse.json({ success: true });
  }, "PATCH /api/organization");
}
