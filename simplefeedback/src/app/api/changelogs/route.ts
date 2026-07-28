import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireUser, requireAdmin, parseBody, getPaginationParams, apiHandler } from "@/lib/api-utils";
import { createChangelogSchema } from "@/lib/schemas";

export async function GET(request: Request) {
  return apiHandler(async () => {
    const auth = await requireUser();
    if (auth.error) return auth.error;

    const { page, limit, skip } = getPaginationParams(new URL(request.url).searchParams);

    const [changelogs, total] = await Promise.all([
      prisma.changelog.findMany({
        where: { organizationId: auth.user.organizationId },
        orderBy: { createdAt: "desc" },
        skip,
        take: limit,
        include: { project: { select: { name: true } } },
      }),
      prisma.changelog.count({ where: { organizationId: auth.user.organizationId } }),
    ]);

    return NextResponse.json({ items: changelogs, total, page, limit, totalPages: Math.ceil(total / limit) });
  }, "GET /api/changelogs");
}

export async function POST(request: Request) {
  return apiHandler(async () => {
    const auth = await requireAdmin();
    if (auth.error) return auth.error;

    const parsed = await parseBody(request, createChangelogSchema);
    if (parsed.error) return parsed.error;

    const { title, content, projectId, publish } = parsed.data;

    const changelog = await prisma.changelog.create({
      data: {
        title,
        content,
        projectId: projectId || null,
        organizationId: auth.user.organizationId,
        publishedAt: publish ? new Date() : null,
      },
    });

    return NextResponse.json(changelog, { status: 201 });
  }, "POST /api/changelogs");
}
