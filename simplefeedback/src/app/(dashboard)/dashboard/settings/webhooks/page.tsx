import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { WebhooksClient } from "./webhooks-client";

export default async function WebhooksPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: { organization: { include: { subscription: true } } },
  });
  if (!dbUser) redirect("/login");

  const plan = dbUser.organization.subscription?.plan || "FREE";
  const hasWebhooks = plan === "PRO" || plan === "BUSINESS";

  const webhooks = await prisma.webhook.findMany({
    where: { organizationId: dbUser.organizationId },
    include: { _count: { select: { deliveries: true } } },
    orderBy: { createdAt: "desc" },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Webhooks</h1>
        <p className="text-neutral-500">
          Send real-time events to your own endpoints
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Webhook Endpoints</CardTitle>
          <CardDescription>
            {hasWebhooks
              ? "Configure webhooks to receive events from SimpleFeedback"
              : "Webhooks require at least a Pro plan"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <WebhooksClient
            webhooks={webhooks}
            hasAccess={hasWebhooks}
            isAdmin={dbUser.role === "ADMIN"}
          />
        </CardContent>
      </Card>
    </div>
  );
}
