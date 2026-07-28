import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { DomainClient } from "./domain-client";

export default async function DomainPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: {
      organization: {
        select: {
          customDomain: true,
          domainVerified: true,
          slug: true,
          subscription: { select: { plan: true } },
        },
      },
    },
  });
  if (!dbUser) redirect("/login");

  const plan = dbUser.organization.subscription?.plan || "FREE";
  const hasCustomDomains = plan === "BUSINESS";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Custom Domain</h1>
        <p className="text-neutral-500">
          Use your own domain for your feedback board
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Domain Configuration</CardTitle>
          <CardDescription>
            {hasCustomDomains
              ? "Configure a custom domain for your public feedback board"
              : "Custom domains require the Business plan"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DomainClient
            currentDomain={dbUser.organization.customDomain}
            isVerified={dbUser.organization.domainVerified}
            orgSlug={dbUser.organization.slug}
            hasAccess={hasCustomDomains}
            isAdmin={dbUser.role === "ADMIN"}
          />
        </CardContent>
      </Card>
    </div>
  );
}
