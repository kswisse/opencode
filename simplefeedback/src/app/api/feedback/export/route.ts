import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { createClient } from "@/lib/supabase-server";

export async function GET(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser) return NextResponse.json({ error: "Not found" }, { status: 404 });

  const { searchParams } = new URL(request.url);
  const status = searchParams.get("status");
  const projectId = searchParams.get("projectId");

  const where: any = { organizationId: dbUser.organizationId };
  if (status && status !== "ALL") where.status = status;
  if (projectId && projectId !== "ALL") where.projectId = projectId;

  const feedback = await prisma.feedback.findMany({
    where,
    orderBy: { createdAt: "desc" },
    include: {
      project: { select: { name: true } },
      author: { select: { name: true, email: true } },
      _count: { select: { votes: true, comments: true } },
    },
  });

  const headers = [
    "ID",
    "Title",
    "Description",
    "Status",
    "Priority",
    "AI Priority Score",
    "Votes",
    "Comments",
    "Project",
    "Author Name",
    "Author Email",
    "Created At",
    "Updated At",
  ];

  const csvRows = feedback.map((fb) => [
    fb.id,
    `"${fb.title.replace(/"/g, '""')}"`,
    `"${(fb.description || "").replace(/"/g, '""')}"`,
    fb.status,
    fb.priority,
    fb.aiPriorityScore?.toString() || "",
    fb._count.votes.toString(),
    fb._count.comments.toString(),
    `"${fb.project.name}"`,
    `"${fb.author.name || ""}"`,
    `"${fb.author.email}"`,
    fb.createdAt.toISOString(),
    fb.updatedAt.toISOString(),
  ]);

  const csv = [
    headers.join(","),
    ...csvRows.map((row) => row.join(",")),
  ].join("\n");

  return new NextResponse(csv, {
    headers: {
      "Content-Type": "text/csv",
      "Content-Disposition": `attachment; filename="feedback-export-${new Date().toISOString().split("T")[0]}.csv"`,
    },
  });
}
