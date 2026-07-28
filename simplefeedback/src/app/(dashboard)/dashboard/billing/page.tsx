import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PLANS } from "@/lib/stripe";
import { ManageSubscription } from "@/components/dashboard/manage-subscription";
import Link from "next/link";
import { Check, Users } from "lucide-react";

export default async function BillingPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: { organization: { include: { subscription: true } } },
  });
  if (!dbUser) redirect("/login");

  const currentPlan = dbUser.organization.subscription?.plan || "FREE";
  const memberCount = await prisma.user.count({
    where: { organizationId: dbUser.organizationId },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Billing</h1>
        <p className="text-neutral-500">Manage your subscription and billing</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-500">Current Plan</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">{PLANS[currentPlan as keyof typeof PLANS].name}</p>
            <p className="text-sm text-neutral-500">${PLANS[currentPlan as keyof typeof PLANS].price}/month</p>
            <div className="mt-2">
              <ManageSubscription
                hasSubscription={!!dbUser.organization.subscription?.stripeSubscriptionId}
                customerId={dbUser.organization.subscription?.stripeCustomerId ?? null}
              />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-500">Team Members</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-neutral-400" />
              <p className="text-lg font-semibold">
                {memberCount} / {PLANS[currentPlan as keyof typeof PLANS].seats}
              </p>
            </div>
            <p className="text-xs text-neutral-500 mt-1">
              {PLANS[currentPlan as keyof typeof PLANS].seats - memberCount} seats remaining
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-500">Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              <p className="text-lg font-semibold">{PLANS[currentPlan as keyof typeof PLANS].projects} projects max</p>
              <p className="text-sm text-neutral-500">
                {PLANS[currentPlan as keyof typeof PLANS].feedbackLimit.toLocaleString()} feedback/mo
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
      {currentPlan === "FREE" && (
        <div className="grid gap-6 md:grid-cols-2">
          {(["PRO", "BUSINESS"] as const).map((plan) => {
            const p = PLANS[plan];
            return (
              <Card key={plan}>
                <CardHeader>
                  <CardTitle>{p.name}</CardTitle>
                  <p className="text-2xl font-bold">${p.price}<span className="text-sm font-normal text-neutral-500">/month</span></p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-500" /> {p.projects} projects</li>
                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-500" /> {p.feedbackLimit.toLocaleString()} feedback items</li>
                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-500" /> {p.seats} team seats</li>
                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-green-500" /> {p.aiFeatures ? "AI features" : "No AI features"}</li>
                  </ul>
                  <form action="/api/checkout" method="POST" className="w-full">
                    <input type="hidden" name="plan" value={plan} />
                    <Button type="submit" className="w-full">
                      Upgrade to {p.name}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
