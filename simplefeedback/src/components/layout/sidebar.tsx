"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Lightbulb,
  RoadIcon,
  Newspaper,
  Settings,
  CreditCard,
  ChevronLeft,
  Menu,
  X,
  Users,
  Shield,
  BarChart3,
} from "lucide-react";
import { useState, useEffect } from "react";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/feedback", label: "Feedback", icon: Lightbulb },
  { href: "/dashboard/roadmap", label: "Roadmap", icon: RoadIcon },
  { href: "/dashboard/changelogs", label: "Changelogs", icon: Newspaper },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
  { href: "/dashboard/billing", label: "Billing", icon: CreditCard },
];

const settingsSubItems = [
  { href: "/dashboard/settings", label: "General", exact: true },
  { href: "/dashboard/settings/members", label: "Members", icon: Users },
  { href: "/dashboard/settings/api-keys", label: "API Keys", icon: Shield },
  { href: "/dashboard/settings/webhooks", label: "Webhooks" },
  { href: "/dashboard/settings/domain", label: "Domain" },
  { href: "/dashboard/settings/audit-log", label: "Audit Log", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close mobile sidebar on navigation
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  const isSettingsActive = pathname.startsWith("/dashboard/settings");

  return (
    <>
      {/* Mobile menu toggle */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed left-4 top-3 z-50 rounded-md p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 lg:hidden"
        aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
      >
        {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
          role="presentation"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "flex flex-col border-r border-neutral-200 bg-white transition-all duration-200 dark:border-neutral-800 dark:bg-neutral-950",
          // Desktop: collapsible
          "hidden lg:flex",
          collapsed ? "w-16" : "w-64",
          // Mobile: overlay
          mobileOpen
            ? "fixed inset-y-0 left-0 z-40 flex w-64"
            : "hidden"
        )}
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="flex h-14 items-center justify-between border-b border-neutral-200 px-4 dark:border-neutral-800">
          {!collapsed && (
            <Link href="/dashboard" className="text-lg font-bold" aria-label="SimpleFeedback Dashboard">
              SimpleFeedback
            </Link>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:block rounded-md p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <ChevronLeft className={cn("h-4 w-4 transition-transform", collapsed && "rotate-180")} />
          </button>
        </div>
        <nav className="flex-1 space-y-1 p-3 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = item.href === "/dashboard/settings"
              ? isSettingsActive
              : (pathname === item.href || pathname.startsWith(item.href + "/"));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-neutral-50"
                    : "text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-50",
                  collapsed && "justify-center"
                )}
                title={collapsed ? item.label : undefined}
                aria-current={isActive ? "page" : undefined}
              >
                <item.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}

          {/* Settings sub-navigation */}
          {isSettingsActive && !collapsed && (
            <div className="ml-6 mt-1 space-y-1 border-l border-neutral-200 dark:border-neutral-700 pl-2">
              {settingsSubItems.map((item) => {
                const isActive = item.exact
                  ? pathname === item.href
                  : pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium transition-colors",
                      isActive
                        ? "text-neutral-900 dark:text-neutral-50"
                        : "text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-300"
                    )}
                  >
                    {item.icon && <item.icon className="h-3 w-3" />}
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          )}
        </nav>

        {/* Usage meter in sidebar footer */}
        {!collapsed && (
          <div className="border-t border-neutral-200 p-4 dark:border-neutral-800">
            <SidebarUsage />
          </div>
        )}
      </aside>

      {/* Mobile bottom navigation */}
      <nav
        className="fixed bottom-0 left-0 right-0 z-20 flex items-center justify-around border-t border-neutral-200 bg-white px-2 py-2 dark:border-neutral-800 dark:bg-neutral-950 lg:hidden"
        role="navigation"
        aria-label="Mobile navigation"
      >
        {navItems.slice(0, 5).map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-1 rounded-md px-3 py-1 text-xs font-medium transition-colors",
                isActive
                  ? "text-neutral-900 dark:text-neutral-50"
                  : "text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <item.icon className="h-5 w-5" aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}

function SidebarUsage() {
  const [usage, setUsage] = useState<{ projects: number; feedback: number; limits: { projects: number; feedbackLimit: number } } | null>(null);

  useEffect(() => {
    fetch("/api/organization")
      .then((r) => r.json())
      .then((data) => {
        setUsage({
          projects: data.projectsCount || 0,
          feedback: data.feedbackCount || 0,
          limits: data.limits || { projects: 1, feedbackLimit: 100 },
        });
      })
      .catch(() => {});
  }, []);

  if (!usage) return null;

  const projectPct = Math.min((usage.projects / usage.limits.projects) * 100, 100);
  const feedbackPct = Math.min((usage.feedback / usage.limits.feedbackLimit) * 100, 100);

  return (
    <div className="space-y-2">
      <Link href="/dashboard/billing" className="block">
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-neutral-500">Projects</span>
            <span className="text-neutral-400">{usage.projects}/{usage.limits.projects}</span>
          </div>
          <div className="h-1.5 w-full bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-neutral-900 dark:bg-neutral-200 rounded-full transition-all"
              style={{ width: `${projectPct}%` }}
            />
          </div>
        </div>
        <div className="space-y-1 mt-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-neutral-500">Feedback</span>
            <span className="text-neutral-400">{usage.feedback}/{usage.limits.feedbackLimit.toLocaleString()}</span>
          </div>
          <div className="h-1.5 w-full bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-neutral-900 dark:bg-neutral-200 rounded-full transition-all"
              style={{ width: `${feedbackPct}%` }}
            />
          </div>
        </div>
      </Link>
    </div>
  );
}
