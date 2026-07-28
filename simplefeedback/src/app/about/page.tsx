import type { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "About - SimpleFeedback",
  description:
    "Learn about SimpleFeedback's mission to help product teams collect, organize, and act on user feedback. Built by developers, for product teams.",
  openGraph: {
    title: "About - SimpleFeedback",
    description:
      "Learn about SimpleFeedback's mission to help product teams collect, organize, and act on user feedback.",
  },
};

const values = [
  {
    title: "User-First Design",
    description:
      "Every feature we build starts with the question: 'How does this help our users better understand their users?'",
  },
  {
    title: "Transparency by Default",
    description:
      "We believe in radical transparency — both in how we build our product and how our customers communicate with their users.",
  },
  {
    title: "AI-Augmented, Not AI-Replaced",
    description:
      "We use AI to enhance human decision-making, not replace it. Our AI helps you find signal in the noise.",
  },
  {
    title: "Privacy First",
    description:
      "Your data is your data. We built SimpleFeedback with privacy and security as foundational principles, not afterthoughts.",
  },
];

const team = [
  { name: "Alex Mercer", role: "Founder & CEO", initials: "AM" },
  { name: "Jordan Lee", role: "CTO", initials: "JL" },
  { name: "Priya Sharma", role: "Head of Product", initials: "PS" },
  { name: "Taylor Brooks", role: "Lead Engineer", initials: "TB" },
];

export default function AboutPage() {
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
        {/* Hero */}
        <section className="mx-auto max-w-4xl px-4 py-20 text-center">
          <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl">
            Building better products,{" "}
            <span className="text-indigo-500">together</span>
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-neutral-600 dark:text-neutral-400">
            SimpleFeedback was born from a simple observation: most product teams
            struggle to collect, organize, and act on user feedback. We set out
            to fix that.
          </p>
        </section>

        {/* Story */}
        <section className="border-t border-neutral-200 py-20 dark:border-neutral-800">
          <div className="mx-auto max-w-3xl px-4">
            <h2 className="mb-8 text-3xl font-bold">Our Story</h2>
            <div className="space-y-4 text-neutral-600 dark:text-neutral-400">
              <p>
                In 2025, our founding team was building a SaaS product and
                realized we were drowning in user feedback. Feature requests came
                through email, Twitter, Intercom, support tickets — there was no
                single source of truth.
              </p>
              <p>
                We tried existing feedback tools, but they were either too
                expensive, too complex, or didn't give our users the transparency
                they deserved. So we built our own.
              </p>
              <p>
                SimpleFeedback launched in early 2026 with a focus on three
                things: simplicity, transparency, and AI-powered insights. We
                wanted a tool that any product team could set up in minutes and
                that would grow with them.
              </p>
              <p>
                Today, thousands of product teams use SimpleFeedback to collect
                feedback, prioritize their roadmap, and keep users in the loop.
                We're proud of what we've built — and we're just getting started.
              </p>
            </div>
          </div>
        </section>

        {/* Values */}
        <section className="border-t border-neutral-200 bg-neutral-50 py-20 dark:border-neutral-800 dark:bg-neutral-900">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="mb-12 text-center text-3xl font-bold">Our Values</h2>
            <div className="grid gap-8 md:grid-cols-2">
              {values.map((value) => (
                <div
                  key={value.title}
                  className="rounded-xl border border-neutral-200 bg-white p-6 dark:border-neutral-700 dark:bg-neutral-950"
                >
                  <h3 className="mb-2 text-lg font-semibold">{value.title}</h3>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {value.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Team */}
        <section className="mx-auto max-w-6xl px-4 py-20">
          <h2 className="mb-12 text-center text-3xl font-bold">Meet the Team</h2>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {team.map((member) => (
              <div key={member.name} className="text-center">
                <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-indigo-100 text-xl font-bold text-indigo-600 dark:bg-indigo-900 dark:text-indigo-300">
                  {member.initials}
                </div>
                <h3 className="font-semibold">{member.name}</h3>
                <p className="text-sm text-neutral-500">{member.role}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="border-t border-neutral-200 bg-indigo-50 py-20 dark:border-neutral-800 dark:bg-indigo-950">
          <div className="mx-auto max-w-2xl px-4 text-center">
            <h2 className="mb-4 text-3xl font-bold">
              Join us on this journey
            </h2>
            <p className="mb-8 text-neutral-600 dark:text-neutral-400">
              Start collecting feedback the right way. Free plan available — no
              credit card required.
            </p>
            <Button size="lg" asChild>
              <Link href="/signup">Get Started Free</Link>
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
