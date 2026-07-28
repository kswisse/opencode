import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireAdmin, parseBody, apiHandler } from "@/lib/api-utils";
import { updateChangelogSchema } from "@/lib/schemas";

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return apiHandler(async () => {
    const { id } = await params;
    const auth = await requireAdmin();
    if (auth.error) return auth.error;

    const parsed = await parseBody(request, updateChangelogSchema);
    if (parsed.error) return parsed.error;

    const { title, content, publish } = parsed.data;

    const data: Record<string, unknown> = {};
    if (title) data.title = title;
    if (content) data.content = content;
    if (publish) data.publishedAt = new Date();

    const result = await prisma.changelog.updateMany({
      where: { id, organizationId: auth.user.organizationId },
      data,
    });

    if (result.count === 0) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    return NextResponse.json({ success: true });
  }, "PATCH /api/changelogs/[id]");
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  return apiHandler(async () => {
    const { id } = await params;
    const auth = await requireAdmin();
    if (auth.error) return auth.error;

    const result = await prisma.changelog.deleteMany({
      where: { id, organizationId: auth.user.organizationId },
    });

    if (result.count === 0) {
      return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    return new NextResponse(null, { status: 204 });
  }, "DELETE /api/changelogs/[id]");
}
