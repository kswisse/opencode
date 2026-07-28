import type { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Features - SimpleFeedback",
  description:
    "Discover everything SimpleFeedback offers: AI-powered analysis, public feedback boards, roadmaps, changelogs, embeddable widgets, and more.",
  openGraph: {
    title: "Features - SimpleFeedback",
    description:
      "Discover everything SimpleFeedback offers: AI-powered analysis, public feedback boards, roadmaps, changelogs, embeddable widgets, and more.",
  },
};

const features = [
  {
    title: "Feedback Board",
    description:
      "A beautiful, public-facing board where your users can submit ideas, report issues, and vote on existing feedback. Fully customizable with your brand colors and logo.",
    benefits: [
      "Customizable branding and styling",
      "Voting and commenting on feedback",
      "Search and filter capabilities",
      "Email verification for spam protection",
    ],
    icon: "📋",
  },
  {
    title: "Public Roadmap",
    description:
      "Build trust with your users by sharing what you're working on. Show planned, in-progress, and completed items in a visually appealing roadmap view.",
    benefits: [
      "Drag-and-drop prioritization",
      "Status tracking (Planned, In Progress, Completed)",
      "Subscribe to updates on specific items",
      "Shareable public URL",
    ],
    icon: "🗺️",
  },
  {
    title: "Automated Changelogs",
    description:
      "Automatically generate beautiful release notes from completed feedback items. Keep your users informed about every update with zero effort.",
    benefits: [
      "AI-generated release notes",
      "Auto-publish when feedback is completed",
      "RSS feed for subscribers",
      "Email notifications on new releases",
    ],
    icon: "📝",
  },
  {
    title: "AI-Powered Analysis",
    description:
      "Our AI engine automatically analyzes every piece of feedback to help you make data-driven decisions about what to build next.",
    benefits: [
      "Automatic duplicate detection",
      "Priority scoring (0-100)",
      "Smart clustering of related feedback",
      "Trend analysis and insights",
    ],
    icon: "🤖",
  },
  {
    title: "Embeddable Widget",
    description:
      "Add a feedback widget to your app with a single line of JavaScript. Collect feedback without context switching for your users.",
    benefits: [
      "One-line JavaScript embed",
      "Customizable position and styling",
      "Screenshot attachment support",
      "Works with any framework",
    ],
    icon: "🔌",
  },
  {
    title: "GitHub Integration",
    description:
      "Connect feedback directly to your development workflow. Automatically create GitHub issues from high-priority feedback.",
    benefits: [
      "Auto-create issues from feedback",
      "Two-way sync with GitHub",
      "Link feedback items to PRs",
      "Custom priority thresholds",
    ],
    icon: "🐙",
  },
  {
    title: "Team Collaboration",
    description:
      "Invite your team to manage feedback together. Assign items, leave internal notes, and keep everyone aligned.",
    benefits: [
      "Team member roles and permissions",
      "Internal notes and discussions",
      "Feedback assignment",
      "Activity audit log",
    ],
    icon: "👥",
  },
  {
    title: "Integrations & API",
    description:
      "Connect SimpleFeedback with the tools you already use. Webhooks and REST API for custom integrations.",
    benefits: [
      "Slack notifications",
      "Zapier integration (coming soon)",
      "RESTful API",
      "Webhooks for custom workflows",
    ],
    icon: "🔗",
  },
  {
    title: "Analytics & Insights",
    description:
      "Understand your feedback data with powerful analytics. Track trends, measure response times, and identify patterns.",
    benefits: [
      "Real-time dashboards",
      "Trend analysis",
      "Response time tracking",
      "Export to CSV/JSON",
    ],
    icon: "📊",
  },
];

export default function FeaturesPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-neutral-200 dark:border-neutral-800">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="text-xl font-bold tracking-tight">
            SimpleFeedback
          </Link>
          <nav className="flex items-center gap-4">
            <Link
              href="/pricing"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              Pricing
            </Link>
            <Link
              href="/login"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              Sign in
            </Link>
            <Button asChild>
              <Link href="/signup">Get Started Free</Link>
            </Button>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-4 py-20 text-center">
          <h1 className="mb-4 text-4xl font-bold tracking-tight sm:text-5xl">
            Everything you need to{" "}
            <span className="text-indigo-500">manage feedback</span>
          </h1>
          <p className="mx-auto mb-12 max-w-2xl text-lg text-neutral-600 dark:text-neutral-400">
            From collection to action — a complete feedback management platform
            for modern product teams.
          </p>
        </section>

        <section className="mx-auto max-w-6xl px-4 pb-20">
          <div className="space-y-24">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className={`flex flex-col gap-12 ${
                  i % 2 === 0 ? "md:flex-row" : "md:flex-row-reverse"
                }`}
              >
                <div className="flex-1">
                  <div className="mb-4 text-4xl">{feature.icon}</div>
                  <h2 className="mb-3 text-2xl font-bold">{feature.title}</h2>
                  <p className="mb-6 text-neutral-600 dark:text-neutral-400">
                    {feature.description}
                  </p>
                  <ul className="space-y-2">
                    {feature.benefits.map((b) => (
                      <li key={b} className="flex items-center gap-2 text-sm">
                        <span className="text-green-500">✓</span>
                        <span className="text-neutral-600 dark:text-neutral-400">{b}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex-1 rounded-2xl border border-neutral-200 bg-neutral-50 p-12 dark:border-neutral-800 dark:bg-neutral-900">
                  <div className="flex h-full items-center justify-center text-neutral-300 dark:text-neutral-600">
                    <div className="text-center">
                      <div className="text-6xl">{feature.icon}</div>
                      <p className="mt-4 text-sm">Interactive preview coming soon</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="border-t border-neutral-200 bg-indigo-50 py-20 dark:border-neutral-800 dark:bg-indigo-950">
          <div className="mx-auto max-w-2xl px-4 text-center">
            <h2 className="mb-4 text-3xl font-bold">Ready to get started?</h2>
            <p className="mb-8 text-neutral-600 dark:text-neutral-400">
              Join thousands of product teams using SimpleFeedback to build
              better products.
            </p>
            <Button size="lg" asChild>
              <Link href="/signup">Start Free Trial</Link>
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t border-neutral-200 py-8 dark:border-neutral-800">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-neutral-500">
          &copy; {new Date().getFullYear()} SimpleFeedback. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
