import { notFound } from "next/navigation";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export const dynamic = "force-dynamic";

export default async function PublicChangelogPage({
  params,
}: {
  params: Promise<{ org: string }>;
}) {
  const { org: orgSlug } = await params;

  const org = await prisma.organization.findUnique({ where: { slug: orgSlug } });
  if (!org) notFound();

  const changelogs = await prisma.changelog.findMany({
    where: { organizationId: org.id, publishedAt: { not: null } },
    orderBy: { publishedAt: "desc" },
    include: { project: { select: { name: true } } },
  });

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold">{org.name} Changelog</h1>
        <p className="mt-2 text-neutral-500">Latest updates and improvements</p>
      </div>
      <div className="space-y-6">
        {changelogs.map((cl) => (
          <Card key={cl.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{cl.title}</CardTitle>
                {cl.publishedAt && (
                  <span className="text-sm text-neutral-400">
                    {formatDate(cl.publishedAt)}
                  </span>
                )}
              </div>
              {cl.project && (
                <p className="text-xs text-neutral-400">{cl.project.name}</p>
              )}
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {cl.content}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        ))}
        {changelogs.length === 0 && (
          <Card>
            <CardContent className="py-8 text-center text-sm text-neutral-500">
              No changelogs published yet.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
