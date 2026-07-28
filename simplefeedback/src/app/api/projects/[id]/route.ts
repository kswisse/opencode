import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireUser, requireAdmin, parseBody, apiHandler } from "@/lib/api-utils";
import { updateProjectSchema } from "@/lib/schemas";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return apiHandler(async () => {
    const { id } = await params;
    const auth = await requireUser();
    if (auth.error) return auth.error;

    const project = await prisma.project.findFirst({
      where: { id, organizationId: auth.user.organizationId },
      include: {
        _count: { select: { feedback: true } },
        feedback: {
          orderBy: { createdAt: "desc" },
          take: 50,
          include: {
            _count: { select: { votes: true, comments: true } },
            author: { select: { name: true, email: true } },
          },
        },
      },
    });

    if (!project) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    return NextResponse.json(project);
  }, "GET /api/projects/[id]");
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return apiHandler(async () => {
    const { id } = await params;
    const auth = await requireAdmin();
    if (auth.error) return auth.error;

    const parsed = await parseBody(request, updateProjectSchema);
    if (parsed.error) return parsed.error;

    const { name, description } = parsed.data;

    const result = await prisma.project.updateMany({
      where: { id, organizationId: auth.user.organizationId },
      data: {
        ...(name && { name }),
        ...(description !== undefined ? { description } : {}),
      },
    });

    if (result.count === 0) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    return NextResponse.json({ success: true });
  }, "PATCH /api/projects/[id]");
}
