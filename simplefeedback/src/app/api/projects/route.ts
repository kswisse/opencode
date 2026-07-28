import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireUser, requireAdmin, parseBody, apiHandler, getPaginationParams } from "@/lib/api-utils";
import { createProjectSchema } from "@/lib/schemas";
import { slugify } from "@/lib/utils";
import { checkProjectLimit } from "@/lib/limits";
import { logger } from "@/lib/logger";

export async function GET() {
  return apiHandler(async () => {
    const auth = await requireUser();
    if (auth.error) return auth.error;

    const projects = await prisma.project.findMany({
      where: { organizationId: auth.user.organizationId },
      include: { _count: { select: { feedback: true } } },
      orderBy: { createdAt: "desc" },
    });

    return NextResponse.json(projects);
  }, "GET /api/projects");
}

export async function POST(request: Request) {
  return apiHandler(async () => {
    const auth = await requireAdmin();
    if (auth.error) return auth.error;

    // Check project limit
    const limitCheck = await checkProjectLimit(auth.user.organizationId);
    if (!limitCheck.allowed) {
      return NextResponse.json({
        error: `Project limit reached (${limitCheck.current}/${limitCheck.limit}). Please upgrade your plan to create more projects.`,
        limitCheck,
      }, { status: 402 });
    }

    const parsed = await parseBody(request, createProjectSchema);
    if (parsed.error) return parsed.error;

    const { name, description } = parsed.data;

    const slug = slugify(name);

    const existing = await prisma.project.findFirst({
      where: { slug, organizationId: auth.user.organizationId },
    });

    const project = await prisma.project.create({
      data: {
        name,
        description: description || null,
        slug: existing ? `${slug}-${Date.now()}` : slug,
        organizationId: auth.user.organizationId,
      },
    });

    return NextResponse.json(project, { status: 201 });
  }, "POST /api/projects");
}
