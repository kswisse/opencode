import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { AuditLogClient } from "./audit-log-client";

export default async function AuditLogPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: { organization: { include: { subscription: { select: { plan: true } } } } },
  });
  if (!dbUser) redirect("/login");

  const plan = dbUser.organization.subscription?.plan || "FREE";
  const hasAuditLogs = plan === "BUSINESS";

  // Only fetch logs if user has access
  const logs = hasAuditLogs
    ? await prisma.auditLog.findMany({
        where: { organizationId: dbUser.organizationId },
        orderBy: { createdAt: "desc" },
        take: 100,
      })
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Audit Log</h1>
        <p className="text-neutral-500">
          Track changes and actions across your organization
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Activity Log</CardTitle>
          <CardDescription>
            {hasAuditLogs
              ? "A chronological record of actions taken within your organization"
              : "Audit logs require the Business plan"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AuditLogClient logs={logs} hasAccess={hasAuditLogs} />
        </CardContent>
      </Card>
    </div>
  );
}
