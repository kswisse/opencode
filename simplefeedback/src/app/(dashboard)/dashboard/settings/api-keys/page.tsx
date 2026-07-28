import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ApiKeysClient } from "./api-keys-client";

export default async function ApiKeysPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: { organization: { include: { subscription: true } } },
  });
  if (!dbUser) redirect("/login");

  const plan = dbUser.organization.subscription?.plan || "FREE";
  const hasApiAccess = plan === "PRO" || plan === "BUSINESS";

  const apiKeys = await prisma.apiKey.findMany({
    where: { organizationId: dbUser.organizationId },
    select: {
      id: true,
      name: true,
      prefix: true,
      active: true,
      lastUsedAt: true,
      expiresAt: true,
      createdAt: true,
    },
    orderBy: { createdAt: "desc" },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">API Keys</h1>
        <p className="text-neutral-500">
          Manage API keys for programmatic access to your feedback data
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>
            {hasApiAccess
              ? "Create and manage API keys to access the SimpleFeedback API"
              : "API access requires at least a Pro plan"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ApiKeysClient
            apiKeys={apiKeys}
            hasAccess={hasApiAccess}
            isAdmin={dbUser.role === "ADMIN"}
          />
        </CardContent>
      </Card>
    </div>
  );
}
