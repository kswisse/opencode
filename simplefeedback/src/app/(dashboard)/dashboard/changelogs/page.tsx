import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { ChangelogsList } from "@/components/dashboard/changelogs-list";

export const dynamic = "force-dynamic";

export default async function ChangelogsPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser) redirect("/login");

  const changelogs = await prisma.changelog.findMany({
    where: { organizationId: dbUser.organizationId },
    orderBy: { createdAt: "desc" },
    include: { project: { select: { name: true } } },
  });

  const serialized = changelogs.map((cl) => ({
    id: cl.id,
    title: cl.title,
    content: cl.content,
    publishedAt: cl.publishedAt?.toISOString() || null,
    createdAt: cl.createdAt.toISOString(),
    project: cl.project,
  }));

  return <ChangelogsList changelogs={serialized} />;
}
