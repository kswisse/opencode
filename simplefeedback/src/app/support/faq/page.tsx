import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "FAQ - SimpleFeedback",
  description: "Frequently asked questions about SimpleFeedback. Find answers to common questions.",
};

const faqs = [
  {
    category: "General",
    items: [
      {
        q: "What is SimpleFeedback?",
        a: "SimpleFeedback is a feedback management platform that helps product teams collect, organize, and act on user feedback. It includes public feedback boards, roadmaps, changelogs, AI-powered analysis, and more.",
      },
      {
        q: "Is there a free plan?",
        a: "Yes! Our Free plan includes 1 project, 100 feedback items per month, a basic feedback board, email notifications, and CSV export. No credit card required.",
      },
      {
        q: "Can I try the Pro plan before paying?",
        a: "Absolutely. The Pro plan includes a 14-day free trial with full access to all features. You can cancel anytime during the trial with no charge.",
      },
    ],
  },
  {
    category: "Account & Billing",
    items: [
      {
        q: "How do I upgrade my plan?",
        a: "Go to your dashboard's billing settings. You can upgrade or downgrade at any time. Upgrades take effect immediately, and downgrades apply at the end of your billing cycle.",
      },
      {
        q: "What payment methods do you accept?",
        a: "We accept all major credit cards (Visa, Mastercard, American Express) and PayPal. Enterprise customers can also pay by invoice.",
      },
      {
        q: "Can I get a refund?",
        a: "All paid plans come with a 30-day money-back guarantee. Contact our support team for a full refund if you're not satisfied.",
      },
    ],
  },
  {
    category: "Features",
    items: [
      {
        q: "How does AI priority scoring work?",
        a: "Our AI analyzes each feedback item's content, title, vote count, and historical patterns to assign a priority score from 0-100. This helps you identify the most impactful items to work on first.",
      },
      {
        q: "Can I customize the feedback widget?",
        a: "Yes. You can customize the widget's button color, text, position, title, subtitle, and more. Pro and Business plans include full widget customization.",
      },
      {
        q: "How does the GitHub integration work?",
        a: "When a feedback item reaches a configurable priority threshold, SimpleFeedback automatically creates a GitHub issue with the feedback details. You can set up multiple repositories and customize labels.",
      },
    ],
  },
  {
    category: "Technical",
    items: [
      {
        q: "Is my data secure?",
        a: "Yes. We use encryption at rest and in transit, regular security audits, and strict access controls. Your data is hosted on secure, SOC 2 compliant infrastructure.",
      },
      {
        q: "Do you offer SSO?",
        a: "Yes, Business plan customers get SSO/SAML support. Contact our sales team to set it up.",
      },
      {
        q: "What is your uptime guarantee?",
        a: "We guarantee 99.9% uptime for all plans. Business plan customers get a 99.99% SLA with credits if we fall short.",
      },
    ],
  },
];

export default function FAQPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-neutral-200 dark:border-neutral-800">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="text-lg font-bold tracking-tight">
            SimpleFeedback
          </Link>
          <nav className="flex items-center gap-4">
            <Link
              href="/support"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              Support
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-12">
        <h1 className="mb-2 text-3xl font-bold">Frequently Asked Questions</h1>
        <p className="mb-12 text-neutral-600 dark:text-neutral-400">
          Everything you need to know about SimpleFeedback.
        </p>

        {/* Search */}
        <div className="mb-12">
          <input
            type="search"
            placeholder="Search FAQ..."
            className="w-full rounded-lg border border-neutral-300 px-4 py-3 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-neutral-700 dark:bg-neutral-900"
          />
        </div>

        {faqs.map((category) => (
          <div key={category.category} className="mb-12">
            <h2 className="mb-6 text-xl font-bold">{category.category}</h2>
            <div className="space-y-3">
              {category.items.map((faq) => (
                <details
                  key={faq.q}
                  className="group rounded-xl border border-neutral-200 transition-all open:border-indigo-200 dark:border-neutral-800 dark:open:border-indigo-800"
                >
                  <summary className="flex cursor-pointer items-center justify-between p-4 font-medium">
                    {faq.q}
                    <svg
                      className="h-5 w-5 shrink-0 text-neutral-400 transition-transform group-open:rotate-180"
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
          </div>
        ))}

        <div className="mt-16 rounded-2xl border border-neutral-200 bg-neutral-50 p-8 text-center dark:border-neutral-800 dark:bg-neutral-900">
          <h2 className="mb-2 text-xl font-bold">Still have questions?</h2>
          <p className="mb-4 text-neutral-600 dark:text-neutral-400">
            Can't find what you're looking for? Reach out to our support team.
          </p>
          <Link
            href="/support"
            className="inline-flex items-center justify-center rounded-md bg-neutral-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-neutral-700 dark:bg-neutral-50 dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            Contact Support
          </Link>
        </div>
      </main>

      <footer className="border-t border-neutral-200 py-8 dark:border-neutral-800">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-neutral-500">
          &copy; {new Date().getFullYear()} SimpleFeedback. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
