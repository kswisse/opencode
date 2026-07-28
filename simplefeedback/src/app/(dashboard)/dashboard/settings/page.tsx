import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { SettingsForm } from "@/components/dashboard/settings-form";
import { WidgetSettings } from "@/components/dashboard/widget-settings";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Users, Key, Webhook, Globe, BarChart3, ArrowRight } from "lucide-react";

export default async function SettingsPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: { organization: { include: { subscription: true } } },
  });
  if (!dbUser) redirect("/login");

  const feedbackEmbed = await prisma.feedbackEmbed.findFirst({
    where: { organizationId: dbUser.organizationId },
  });

  const projects = await prisma.project.findMany({
    where: { organizationId: dbUser.organizationId },
    select: { id: true, name: true },
  });

  const plan = dbUser.organization.subscription?.plan || "FREE";
  const isAdmin = dbUser.role === "ADMIN";

  const settingsLinks = [
    {
      href: "/dashboard/settings/members",
      label: "Team Members",
      description: "Manage team members and roles",
      icon: Users,
      badge: null,
    },
    {
      href: "/dashboard/settings/api-keys",
      label: "API Keys",
      description: "Manage API access",
      icon: Key,
      badge: plan === "FREE" ? "Pro" : null,
    },
    {
      href: "/dashboard/settings/webhooks",
      label: "Webhooks",
      description: "Configure webhook endpoints",
      icon: Webhook,
      badge: plan === "FREE" ? "Pro" : null,
    },
    {
      href: "/dashboard/settings/domain",
      label: "Custom Domain",
      description: "Use your own domain",
      icon: Globe,
      badge: plan !== "BUSINESS" ? "Business" : null,
    },
    {
      href: "/dashboard/settings/audit-log",
      label: "Audit Log",
      description: "Track organization changes",
      icon: BarChart3,
      badge: plan !== "BUSINESS" ? "Business" : null,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-neutral-500">Manage your organization settings</p>
      </div>

      {/* Settings navigation grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {settingsLinks.map((link) => (
          <Link key={link.href} href={link.href}>
            <Card className="h-full hover:border-neutral-300 dark:hover:border-neutral-700 transition-colors cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-neutral-100 dark:bg-neutral-800">
                      <link.icon className="h-5 w-5 text-neutral-600 dark:text-neutral-400" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">{link.label}</p>
                      <p className="text-xs text-neutral-500">{link.description}</p>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-neutral-300 mt-2 shrink-0" />
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Organization settings */}
      <Card>
        <CardHeader>
          <CardTitle>Organization</CardTitle>
          <CardDescription>Update your organization name and profile</CardDescription>
        </CardHeader>
        <CardContent>
          <SettingsForm
            organization={{ name: dbUser.organization.name, slug: dbUser.organization.slug }}
            user={{ name: dbUser.name, email: dbUser.email }}
          />
        </CardContent>
      </Card>

      {/* Feedback Widget */}
      <Card>
        <CardHeader>
          <CardTitle>Feedback Widget</CardTitle>
          <CardDescription>Customize the embedded feedback widget</CardDescription>
        </CardHeader>
        <CardContent>
          <WidgetSettings
            embed={feedbackEmbed ? {
              projectId: feedbackEmbed.projectId,
              buttonColor: feedbackEmbed.buttonColor,
              buttonText: feedbackEmbed.buttonText,
              position: feedbackEmbed.position,
              title: feedbackEmbed.title,
              subtitle: feedbackEmbed.subtitle,
            } : null}
            projects={projects}
            orgSlug={dbUser.organization.slug}
          />
        </CardContent>
      </Card>
    </div>
  );
}
