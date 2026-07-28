import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { FeedbackList } from "@/components/feedback/feedback-list";

export const dynamic = "force-dynamic";

export default async function FeedbackPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser) redirect("/login");

  const feedbackItems = await prisma.feedback.findMany({
    where: { organizationId: dbUser.organizationId },
    orderBy: { createdAt: "desc" },
    include: {
      project: { select: { name: true, id: true } },
      author: { select: { name: true, email: true } },
      _count: { select: { votes: true, comments: true } },
    },
  });

  const projects = await prisma.project.findMany({
    where: { organizationId: dbUser.organizationId },
    select: { id: true, name: true },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Feedback</h1>
        <p className="text-neutral-500">View and manage all user feedback</p>
      </div>
      <FeedbackList feedbackItems={feedbackItems} projects={projects} />
    </div>
  );
}
