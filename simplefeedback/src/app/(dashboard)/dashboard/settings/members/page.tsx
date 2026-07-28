import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { MembersClient } from "./members-client";

export default async function MembersPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: { organization: { include: { subscription: true } } },
  });
  if (!dbUser) redirect("/login");

  const members = await prisma.user.findMany({
    where: { organizationId: dbUser.organizationId },
    select: {
      id: true,
      email: true,
      name: true,
      avatarUrl: true,
      role: true,
      createdAt: true,
    },
    orderBy: { createdAt: "asc" },
  });

  const pendingInvites = await prisma.invite.findMany({
    where: { organizationId: dbUser.organizationId, status: "PENDING" },
    select: {
      id: true,
      email: true,
      role: true,
      createdAt: true,
      expiresAt: true,
    },
    orderBy: { createdAt: "desc" },
  });

  const plan = dbUser.organization.subscription?.plan || "FREE";
  const seatLimit = plan === "FREE" ? 1 : plan === "PRO" ? 5 : 50;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Team Members</h1>
        <p className="text-neutral-500">
          Manage your team members and their roles ({members.length}/{seatLimit} seats used)
        </p>
      </div>

      <MembersClient
        members={members}
        pendingInvites={pendingInvites}
        currentUserId={dbUser.id}
        isAdmin={dbUser.role === "ADMIN"}
        seatLimit={seatLimit}
        currentSeats={members.length}
        plan={plan}
      />
    </div>
  );
}
