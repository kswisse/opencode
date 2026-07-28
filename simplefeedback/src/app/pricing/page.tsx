import type { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Pricing - SimpleFeedback",
  description:
    "Simple, transparent pricing for teams of all sizes. Start free, upgrade when you need more. All plans include a 30-day money-back guarantee.",
  openGraph: {
    title: "Pricing - SimpleFeedback",
    description:
      "Simple, transparent pricing for teams of all sizes. Start free, upgrade when you need more.",
  },
};

const plans = [
  {
    name: "Free",
    price: "$0",
    description: "Perfect for getting started with feedback collection.",
    features: [
      "1 project",
      "100 feedback items per month",
      "Basic feedback board",
      "Email notifications",
      "CSV export",
      "Community support",
    ],
    cta: "Get Started",
    href: "/signup",
    popular: false,
  },
  {
    name: "Pro",
    price: "$29",
    description: "For growing teams that need powerful feedback tools.",
    features: [
      "10 projects",
      "5,000 feedback items per month",
      "AI-powered priority scoring",
      "AI duplicate detection",
      "AI clustering",
      "Custom domain",
      "Widget customization",
      "Public roadmap board",
      "Automated changelogs",
      "GitHub integration",
      "Priority email support",
    ],
    cta: "Start 14-Day Free Trial",
    href: "/signup?plan=pro",
    popular: true,
  },
  {
    name: "Business",
    price: "$99",
    description: "For organizations that need scale and control.",
    features: [
      "50 projects",
      "50,000 feedback items per month",
      "Everything in Pro",
      "SSO & SAML",
      "API access",
      "Webhooks",
      "Audit logs",
      "Dedicated account manager",
      "Custom SLA",
      "99.99% uptime SLA",
      "Priority support with 1hr response",
    ],
    cta: "Contact Sales",
    href: "/contact",
    popular: false,
  },
];

const faqs = [
  {
    q: "Can I upgrade or downgrade my plan at any time?",
    a: "Yes, you can change your plan at any time. Upgrades take effect immediately, and downgrades apply at the end of your billing cycle.",
  },
  {
    q: "Is there a free trial for paid plans?",
    a: "Yes! The Pro plan includes a 14-day free trial with full access to all features. No credit card required to start.",
  },
  {
    q: "What happens when I hit my feedback limit?",
    a: "We'll notify you before you reach your limit. You can upgrade your plan at any time to increase your limit. We never delete your feedback.",
  },
  {
    q: "Do you offer discounts for annual billing?",
    a: "Yes, annual billing gives you 2 months free (17% discount). Contact us for enterprise pricing with custom terms.",
  },
  {
    q: "Can I cancel my subscription?",
    a: "Absolutely. You can cancel anytime from your billing settings. Your data remains accessible, and you can restart anytime.",
  },
];

export default function PricingPage() {
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
        {/* Pricing Header */}
        <section className="mx-auto max-w-6xl px-4 py-20 text-center">
          <h1 className="mb-4 text-4xl font-bold tracking-tight sm:text-5xl">
            Simple, transparent pricing
          </h1>
          <p className="mx-auto mb-8 max-w-2xl text-lg text-neutral-600 dark:text-neutral-400">
            Start free, upgrade when you need more. All plans include a 30-day
            money-back guarantee.
          </p>

          {/* Annual vs Monthly Toggle */}
          <div className="mb-12 inline-flex items-center gap-3 rounded-full border border-neutral-200 bg-neutral-50 p-1 dark:border-neutral-700 dark:bg-neutral-900">
            <button className="rounded-full bg-white px-4 py-2 text-sm font-medium shadow-sm dark:bg-neutral-800">
              Monthly
            </button>
            <button className="rounded-full px-4 py-2 text-sm font-medium text-neutral-500">
              Annual{" "}
              <span className="ml-1 text-xs text-green-500">Save 17%</span>
            </button>
          </div>

          {/* Pricing Cards */}
          <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-3">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`relative flex flex-col rounded-2xl border p-8 text-left ${
                  plan.popular
                    ? "border-indigo-500 ring-2 ring-indigo-500"
                    : "border-neutral-200 dark:border-neutral-800"
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-indigo-500 px-4 py-1 text-xs font-semibold text-white">
                    Most Popular
                  </div>
                )}
                <h2 className="text-xl font-semibold">{plan.name}</h2>
                <div className="mt-3">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-neutral-500">/month</span>
                </div>
                <p className="mt-2 text-sm text-neutral-500">{plan.description}</p>

                <div className="mt-2 flex items-center gap-1 text-xs text-green-600">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  30-day money-back guarantee
                </div>

                <ul className="mt-8 flex-1 space-y-3">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <span className="mt-0.5 text-green-500">✓</span>
                      <span className="text-neutral-600 dark:text-neutral-400">{f}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  className="mt-8 w-full"
                  variant={plan.popular ? "default" : "outline"}
                  size="lg"
                  asChild
                >
                  <Link href={plan.href}>{plan.cta}</Link>
                </Button>
              </div>
            ))}
          </div>
        </section>

        {/* Enterprise Section */}
        <section className="border-t border-neutral-200 bg-neutral-50 py-20 dark:border-neutral-800 dark:bg-neutral-900">
          <div className="mx-auto max-w-4xl px-4 text-center">
            <h2 className="mb-4 text-3xl font-bold">Need a custom plan?</h2>
            <p className="mx-auto mb-8 max-w-2xl text-neutral-600 dark:text-neutral-400">
              We offer custom pricing for large teams with specific requirements.
              Contact our sales team for a tailored solution.
            </p>
            <Button size="lg" variant="outline" asChild>
              <Link href="/contact">Contact Sales</Link>
            </Button>
          </div>
        </section>

        {/* FAQ */}
        <section className="mx-auto max-w-3xl px-4 py-20">
          <h2 className="mb-12 text-center text-3xl font-bold">
            Frequently asked questions
          </h2>
          <div className="space-y-4">
            {faqs.map((faq) => (
              <details
                key={faq.q}
                className="group rounded-xl border border-neutral-200 transition-all open:border-indigo-200 dark:border-neutral-800 dark:open:border-indigo-800"
              >
                <summary className="flex cursor-pointer items-center justify-between p-4 font-medium">
                  {faq.q}
                  <svg
                    className="h-5 w-5 text-neutral-400 transition-transform group-open:rotate-180"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </summary>
                <div className="border-t border-neutral-100 px-4 pb-4 pt-3 text-sm text-neutral-600 dark:border-neutral-800 dark:text-neutral-400">
                  {faq.a}
                </div>
              </details>
            ))}
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
