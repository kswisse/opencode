import type { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Support - SimpleFeedback",
  description: "Get help with SimpleFeedback. Browse our knowledge base, FAQ, or submit a support ticket.",
};

const categories = [
  {
    title: "Getting Started",
    description: "New to SimpleFeedback? Start here.",
    articles: [
      "How to create your first project",
      "Setting up your feedback board",
      "Inviting team members",
      "Understanding feedback statuses",
    ],
  },
  {
    title: "Widget & Integration",
    description: "Install and configure the feedback widget.",
    articles: [
      "Installing the widget",
      "Customizing widget appearance",
      "GitHub integration setup",
      "Slack integration setup",
    ],
  },
  {
    title: "Account & Billing",
    description: "Manage your account and subscription.",
    articles: [
      "Upgrading your plan",
      "Cancelling your subscription",
      "Billing and invoices",
      "Managing team members",
    ],
  },
  {
    title: "Troubleshooting",
    description: "Common issues and how to fix them.",
    articles: [
      "Widget not appearing",
      "Email notifications not sending",
      "GitHub sync issues",
      "API rate limiting",
    ],
  },
];

export default function SupportPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-neutral-200 dark:border-neutral-800">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="text-lg font-bold tracking-tight">
            SimpleFeedback
          </Link>
          <nav className="flex items-center gap-4">
            <Link
              href="/docs"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              Docs
            </Link>
            <Link
              href="/support/faq"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              FAQ
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-4 py-16 text-center">
          <h1 className="mb-4 text-4xl font-bold">How can we help you?</h1>
          <p className="mx-auto mb-8 max-w-xl text-neutral-600 dark:text-neutral-400">
            Search our knowledge base or submit a ticket and we'll get back to you.
          </p>
          <div className="mx-auto max-w-lg">
            <input
              type="search"
              placeholder="Search for answers..."
              className="w-full rounded-lg border border-neutral-300 px-4 py-3 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-neutral-700 dark:bg-neutral-900"
            />
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 pb-8">
          <div className="grid gap-8 md:grid-cols-2">
            {categories.map((cat) => (
              <div
                key={cat.title}
                className="rounded-xl border border-neutral-200 p-6 dark:border-neutral-800"
              >
                <h2 className="mb-1 text-lg font-semibold">{cat.title}</h2>
                <p className="mb-4 text-sm text-neutral-500">{cat.description}</p>
                <ul className="space-y-2">
                  {cat.articles.map((article) => (
                    <li key={article}>
                      <Link
                        href="#"
                        className="text-sm text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                      >
                        {article}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-3xl px-4 py-16">
          <div className="rounded-2xl border border-neutral-200 p-8 dark:border-neutral-800">
            <h2 className="mb-6 text-2xl font-bold">Submit a Support Ticket</h2>
            <form className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="name" className="mb-1 block text-sm font-medium">
                    Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    required
                    className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-neutral-700 dark:bg-neutral-900"
                  />
                </div>
                <div>
                  <label htmlFor="email" className="mb-1 block text-sm font-medium">
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    required
                    className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-neutral-700 dark:bg-neutral-900"
                  />
                </div>
              </div>
              <div>
                <label htmlFor="subject" className="mb-1 block text-sm font-medium">
                  Subject
                </label>
                <input
                  id="subject"
                  type="text"
                  required
                  className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-neutral-700 dark:bg-neutral-900"
                />
              </div>
              <div>
                <label htmlFor="message" className="mb-1 block text-sm font-medium">
                  Message
                </label>
                <textarea
                  id="message"
                  rows={5}
                  required
                  className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-neutral-700 dark:bg-neutral-900"
                />
              </div>
              <Button type="submit" className="w-full sm:w-auto">
                Submit Ticket
              </Button>
            </form>
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
