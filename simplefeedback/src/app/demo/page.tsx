import type { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Try SimpleFeedback Demo",
  description:
    "Experience SimpleFeedback without creating an account. Explore our demo environment with sample data.",
  openGraph: {
    title: "Try SimpleFeedback Demo",
    description:
      "Experience SimpleFeedback without creating an account. Explore our demo environment with sample data.",
  },
};

export default function DemoPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-neutral-200 dark:border-neutral-800">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="text-xl font-bold tracking-tight">
            SimpleFeedback
          </Link>
          <nav className="flex items-center gap-4">
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
        <section className="mx-auto max-w-4xl px-4 py-20 text-center">
          <div className="mb-6 inline-flex items-center rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5 text-sm font-medium text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-300">
            🎮 No account required
          </div>
          <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl">
            Try SimpleFeedback <span className="text-indigo-500">Live Demo</span>
          </h1>
          <p className="mx-auto mb-8 max-w-2xl text-lg text-neutral-600 dark:text-neutral-400">
            Explore our demo environment with pre-loaded data. See how feedback
            collection, AI analysis, roadmaps, and changelogs work in real-time.
          </p>
          <Button size="lg" asChild>
            <Link href="https://demo.simplefeedback.com">
              Launch Demo Environment
            </Link>
          </Button>
        </section>

        {/* Demo Features */}
        <section className="border-t border-neutral-200 bg-neutral-50 py-20 dark:border-neutral-800 dark:bg-neutral-900">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="mb-12 text-center text-3xl font-bold">
              What you can explore
            </h2>
            <div className="grid gap-8 md:grid-cols-3">
              {[
                {
                  title: "Feedback Board",
                  description:
                    "Browse sample feedback items with votes, comments, and AI-powered priority scores.",
                  icon: "📋",
                },
                {
                  title: "Roadmap View",
                  description:
                    "See how planned, in-progress, and completed items are organized on the roadmap.",
                  icon: "🗺️",
                },
                {
                  title: "Admin Dashboard",
                  description:
                    "Try the full admin interface with analytics, settings, and team management.",
                  icon: "⚙️",
                },
              ].map((item) => (
                <div
                  key={item.title}
                  className="rounded-xl border border-neutral-200 bg-white p-6 text-center dark:border-neutral-700 dark:bg-neutral-950"
                >
                  <div className="mb-3 text-3xl">{item.icon}</div>
                  <h3 className="mb-2 font-semibold">{item.title}</h3>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-2xl px-4 py-20 text-center">
          <h2 className="mb-4 text-3xl font-bold">Ready to get started?</h2>
          <p className="mb-8 text-neutral-600 dark:text-neutral-400">
            Create your free account and start collecting feedback in minutes.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="/signup">Sign Up Free</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/">Learn More</Link>
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
