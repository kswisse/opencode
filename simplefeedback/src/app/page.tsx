import Link from "next/link";
import { Button } from "@/components/ui/button";

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "SimpleFeedback",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  description:
    "The simplest way to collect, organize, and act on user feedback. Public boards, roadmaps, changelogs, and AI-powered insights.",
  offers: {
    "@type": "AggregateOffer",
    lowPrice: "0",
    highPrice: "99",
    priceCurrency: "USD",
  },
  aggregateRating: {
    "@type": "AggregateRating",
    ratingValue: "4.8",
    ratingCount: "256",
  },
};

const testimonials = [
  {
    quote: "SimpleFeedback has transformed how we collect and prioritize user feedback. Our response time to customer requests dropped by 60%.",
    name: "Sarah Chen",
    role: "Product Manager",
    company: "TechFlow",
  },
  {
    quote: "The AI-powered duplicate detection alone saves us hours every week. We can finally focus on building what users actually want.",
    name: "Marcus Johnson",
    role: "Founder",
    company: "BuildRight",
  },
  {
    quote: "Our users love the public roadmap. It's built incredible trust and transparency with our customer base.",
    name: "Emily Rodriguez",
    role: "CEO",
    company: "Nexus SaaS",
  },
];

const customerLogos = [
  "TechFlow",
  "BuildRight",
  "Nexus SaaS",
  "DataPulse",
  "CloudHarbor",
  "StackCraft",
];

const faqs = [
  {
    q: "How does the AI-powered priority scoring work?",
    a: "Our AI analyzes each feedback item's content, vote count, and historical patterns to assign a priority score from 0-100. This helps you focus on what matters most to your users.",
  },
  {
    q: "Can I customize the feedback widget to match my brand?",
    a: "Absolutely! You can customize colors, text, position, and more. The widget is designed to seamlessly blend with your existing UI.",
  },
  {
    q: "Is there a free plan available?",
    a: "Yes! Our Free plan includes 1 project, up to 100 feedback items, a basic feedback board, and email notifications. No credit card required.",
  },
  {
    q: "How does the GitHub integration work?",
    a: "High-priority feedback can be automatically pushed to GitHub issues. Connect your repositories and configure the priority threshold — we handle the rest.",
  },
  {
    q: "Can I export my feedback data?",
    a: "Yes, all plans include CSV export. Pro and Business plans also include API access for custom integrations.",
  },
  {
    q: "What kind of support do you offer?",
    a: "Free and Pro plans include email support. Business plans include priority support with guaranteed response times. All plans have access to our documentation and community.",
  },
];

function calculateROI(
  monthlyVisitors: number,
  feedbackRate: number,
  teamSize: number,
  hourlyRate: number
) {
  const monthlyFeedback = monthlyVisitors * (feedbackRate / 100);
  const hoursSavedPerItem = 0.5; // 30 min saved per item with automation
  const monthlyHoursSaved = monthlyFeedback * hoursSavedPerItem;
  const monthlyCostSavings = monthlyHoursSaved * hourlyRate;
  const annualSavings = monthlyCostSavings * 12;
  return {
    monthlyFeedback: Math.round(monthlyFeedback),
    monthlyHoursSaved: Math.round(monthlyHoursSaved),
    monthlyCostSavings: Math.round(monthlyCostSavings),
    annualSavings: Math.round(annualSavings),
  };
}

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* JSON-LD Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Header */}
      <header className="border-b border-neutral-200 dark:border-neutral-800">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="text-xl font-bold tracking-tight">
            SimpleFeedback
          </Link>
          {/* Desktop nav */}
          <nav className="hidden items-center gap-4 sm:flex">
            <Link
              href="/features"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              Features
            </Link>
            <Link
              href="/pricing"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              Pricing
            </Link>
            <Link
              href="/docs"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              Docs
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
          {/* Mobile nav toggle */}
          <details className="sm:hidden">
            <summary className="flex cursor-pointer items-center gap-1 rounded-md px-2 py-1 text-sm text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </summary>
            <div className="absolute left-0 right-0 top-16 z-50 border-b border-neutral-200 bg-white p-4 shadow-lg dark:border-neutral-800 dark:bg-neutral-950">
              <div className="flex flex-col gap-3">
                <Link href="/features" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 dark:text-neutral-400">
                  Features
                </Link>
                <Link href="/pricing" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 dark:text-neutral-400">
                  Pricing
                </Link>
                <Link href="/docs" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 dark:text-neutral-400">
                  Docs
                </Link>
                <Link href="/login" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 dark:text-neutral-400">
                  Sign in
                </Link>
                <Button asChild className="w-full">
                  <Link href="/signup">Get Started Free</Link>
                </Button>
              </div>
            </div>
          </details>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="mx-auto max-w-6xl px-4 py-24 text-center">
          <div className="mb-6 inline-flex items-center rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5 text-sm font-medium text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-300">
            🎉 New: AI-powered feedback analysis is now live!
          </div>
          <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            Collect, Organize, and Act on{" "}
            <span className="text-indigo-500">User Feedback</span>
          </h1>
          <p className="mx-auto mb-8 max-w-2xl text-lg text-neutral-600 dark:text-neutral-400">
            The simplest way to collect feedback from your users, prioritize what matters,
            and keep them in the loop with automated changelogs.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Button size="lg" asChild>
              <Link href="/signup">Start Free Trial</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/demo">Try Live Demo</Link>
            </Button>
          </div>
          <p className="mt-4 text-sm text-neutral-400">No credit card required &middot; Free plan available</p>

          {/* Social Proof - Usage Stats */}
          <div className="mx-auto mt-16 grid max-w-3xl grid-cols-3 gap-8 border-t border-neutral-200 pt-12 dark:border-neutral-800">
            {[
              { value: "10K+", label: "Active Users" },
              { value: "100K+", label: "Feedback Items" },
              { value: "99.9%", label: "Uptime" },
            ].map((stat) => (
              <div key={stat.label}>
                <div className="text-3xl font-bold text-indigo-500">{stat.value}</div>
                <div className="mt-1 text-sm text-neutral-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Customer Logos */}
        <section className="border-t border-neutral-200 py-16 dark:border-neutral-800">
          <div className="mx-auto max-w-6xl px-4 text-center">
            <p className="mb-8 text-sm font-medium uppercase tracking-wider text-neutral-400">
              Trusted by innovative teams
            </p>
            <div className="flex flex-wrap items-center justify-center gap-12">
              {customerLogos.map((logo) => (
                <div
                  key={logo}
                  className="text-lg font-bold text-neutral-300 dark:text-neutral-600"
                >
                  {logo}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section id="features" className="border-t border-neutral-200 py-24 dark:border-neutral-800">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="mb-4 text-center text-3xl font-bold">
              Everything you need to manage feedback
            </h2>
            <p className="mx-auto mb-12 max-w-2xl text-center text-neutral-600 dark:text-neutral-400">
              From collection to action — a complete feedback management platform for modern teams.
            </p>
            <div className="grid gap-8 md:grid-cols-3">
              {[
                {
                  title: "Feedback Board",
                  description:
                    "A public board where users can submit and vote on feedback. Fully customizable to match your brand.",
                  icon: "📋",
                },
                {
                  title: "Public Roadmap",
                  description:
                    "Show your users what's planned, in progress, and completed. Build trust through transparency.",
                  icon: "🗺️",
                },
                {
                  title: "Changelogs",
                  description:
                    "Automatically generate release notes from completed feedback. Keep users informed with every update.",
                  icon: "📝",
                },
                {
                  title: "AI-Powered Analysis",
                  description:
                    "Auto-detect duplicates, score priority, cluster similar feedback, and generate release notes with AI.",
                  icon: "🤖",
                },
                {
                  title: "Embeddable Widget",
                  description:
                    "Add a feedback widget to your app with a single line of JavaScript. Collect feedback without context switching.",
                  icon: "🔌",
                },
                {
                  title: "GitHub Integration",
                  description:
                    "Push high-priority feedback to GitHub issues automatically. Connect feedback to your development workflow.",
                  icon: "🐙",
                },
              ].map((feature) => (
                <div
                  key={feature.title}
                  className="group rounded-xl border border-neutral-200 p-6 transition-all hover:border-indigo-200 hover:shadow-sm dark:border-neutral-800 dark:hover:border-indigo-800"
                >
                  <div className="mb-3 text-2xl">{feature.icon}</div>
                  <h3 className="mb-2 font-semibold">{feature.title}</h3>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Feature Comparison Table */}
        <section className="border-t border-neutral-200 py-24 dark:border-neutral-800">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="mb-4 text-center text-3xl font-bold">
              How we compare
            </h2>
            <p className="mx-auto mb-12 max-w-2xl text-center text-neutral-600 dark:text-neutral-400">
              See how SimpleFeedback stacks up against the competition.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 dark:border-neutral-800">
                    <th className="pb-4 pr-4 font-semibold">Feature</th>
                    <th className="pb-4 pr-4 font-semibold text-indigo-600">SimpleFeedback</th>
                    <th className="pb-4 pr-4 font-semibold text-neutral-400">Canny</th>
                    <th className="pb-4 font-semibold text-neutral-400">Productboard</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
                  {[
                    { feature: "AI Priority Scoring", us: true, them1: false, them2: "Paid" },
                    { feature: "Public Roadmap", us: true, them1: true, them2: true },
                    { feature: "Embeddable Widget", us: true, them1: true, them2: true },
                    { feature: "GitHub Integration", us: true, them1: true, them2: "Paid" },
                    { feature: "Free Plan", us: true, them1: false, them2: false },
                    { feature: "Custom Domain", us: "Pro+", them1: "Paid", them2: "Paid" },
                    { feature: "AI-Powered Clustering", us: true, them1: false, them2: "Paid" },
                    { feature: "API Access", us: "Business+", them1: "Paid", them2: true },
                  ].map((row) => (
                    <tr key={row.feature}>
                      <td className="py-3 pr-4 font-medium">{row.feature}</td>
                      <td className="py-3 pr-4">
                        {row.us === true ? (
                          <span className="text-green-500">✓</span>
                        ) : (
                          <span className="text-sm text-neutral-400">{String(row.us)}</span>
                        )}
                      </td>
                      <td className="py-3 pr-4">
                        {row.them1 === true ? (
                          <span className="text-green-500">✓</span>
                        ) : (
                          <span className="text-sm text-neutral-400">{String(row.them1)}</span>
                        )}
                      </td>
                      <td className="py-3">
                        {row.them2 === true ? (
                          <span className="text-green-500">✓</span>
                        ) : (
                          <span className="text-sm text-neutral-400">{String(row.them2)}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* ROI Calculator */}
        <section className="border-t border-neutral-200 bg-neutral-50 py-24 dark:border-neutral-800 dark:bg-neutral-900">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="mb-4 text-center text-3xl font-bold">
              Calculate your ROI
            </h2>
            <p className="mx-auto mb-12 max-w-2xl text-center text-neutral-600 dark:text-neutral-400">
              See how much time and money your team can save with SimpleFeedback.
            </p>
            <div className="mx-auto max-w-3xl rounded-2xl border border-neutral-200 bg-white p-8 dark:border-neutral-700 dark:bg-neutral-950">
              <div className="grid gap-6 sm:grid-cols-3">
                <div>
                  <label className="mb-2 block text-sm font-medium text-neutral-600">
                    Monthly Visitors
                  </label>
                  <div className="text-2xl font-bold text-indigo-500">10,000</div>
                  <p className="mt-1 text-xs text-neutral-400">Average monthly active users</p>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-neutral-600">
                    Feedback Rate
                  </label>
                  <div className="text-2xl font-bold text-indigo-500">5%</div>
                  <p className="mt-1 text-xs text-neutral-400">% of users who submit feedback</p>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-neutral-600">
                    Team Hourly Rate
                  </label>
                  <div className="text-2xl font-bold text-indigo-500">$75</div>
                  <p className="mt-1 text-xs text-neutral-400">Average loaded cost</p>
                </div>
              </div>
              <div className="mt-8 border-t border-neutral-200 pt-8 dark:border-neutral-700">
                <div className="grid gap-6 text-center sm:grid-cols-3">
                  <div>
                    <div className="text-sm text-neutral-500">Monthly Feedback</div>
                    <div className="text-2xl font-bold">500 items</div>
                  </div>
                  <div>
                    <div className="text-sm text-neutral-500">Hours Saved / Month</div>
                    <div className="text-2xl font-bold text-green-500">250 hrs</div>
                  </div>
                  <div>
                    <div className="text-sm text-neutral-500">Annual Savings</div>
                    <div className="text-2xl font-bold text-green-500">$225,000</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Testimonials */}
        <section className="border-t border-neutral-200 py-24 dark:border-neutral-800">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="mb-12 text-center text-3xl font-bold">
              Loved by product teams
            </h2>
            <div className="grid gap-8 md:grid-cols-3">
              {testimonials.map((t) => (
                <div
                  key={t.name}
                  className="rounded-xl border border-neutral-200 p-6 dark:border-neutral-800"
                >
                  <p className="mb-6 text-sm italic text-neutral-600 dark:text-neutral-400">
                    &ldquo;{t.quote}&rdquo;
                  </p>
                  <div>
                    <div className="font-semibold">{t.name}</div>
                    <div className="text-sm text-neutral-500">
                      {t.role}, {t.company}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className="border-t border-neutral-200 py-24 dark:border-neutral-800">
          <div className="mx-auto max-w-3xl px-4">
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
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="border-t border-neutral-200 py-24 dark:border-neutral-800">
          <div className="mx-auto max-w-6xl px-4 text-center">
            <h2 className="mb-4 text-3xl font-bold">Simple, transparent pricing</h2>
            <p className="mx-auto mb-12 max-w-2xl text-neutral-600 dark:text-neutral-400">
              Start free, upgrade when you need more. All plans include a 30-day money-back guarantee.
            </p>
            <div className="mx-auto grid max-w-4xl gap-8 md:grid-cols-3">
              {[
                {
                  name: "Free",
                  price: "$0",
                  badge: null,
                  features: [
                    "1 project",
                    "100 feedback items",
                    "Basic feedback board",
                    "Email notifications",
                    "CSV export",
                  ],
                  cta: "Get Started",
                  popular: false,
                },
                {
                  name: "Pro",
                  price: "$29",
                  badge: "Most Popular",
                  features: [
                    "10 projects",
                    "5,000 feedback items",
                    "AI-powered features",
                    "Custom domain",
                    "Widget customization",
                    "Public roadmap board",
                    "Priority support",
                  ],
                  cta: "Start 14-Day Trial",
                  popular: true,
                },
                {
                  name: "Business",
                  price: "$99",
                  badge: null,
                  features: [
                    "50 projects",
                    "50,000 feedback items",
                    "Everything in Pro",
                    "SSO & SAML",
                    "API access",
                    "Dedicated support",
                    "SLA guarantee",
                  ],
                  cta: "Contact Sales",
                  popular: false,
                },
              ].map((plan) => (
                <div
                  key={plan.name}
                  className={`relative rounded-xl border p-6 text-left ${
                    plan.popular
                      ? "border-indigo-500 ring-1 ring-indigo-500"
                      : "border-neutral-200 dark:border-neutral-800"
                  }`}
                >
                  {plan.badge && (
                    <div className="mb-4 inline-block rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-700">
                      {plan.badge}
                    </div>
                  )}
                  <h3 className="text-lg font-semibold">{plan.name}</h3>
                  <div className="mt-2 mb-1">
                    <span className="text-3xl font-bold">{plan.price}</span>
                    <span className="text-neutral-500">/month</span>
                  </div>
                  <div className="mb-6 text-xs text-neutral-400">30-day money-back guarantee</div>
                  <ul className="mb-8 space-y-2 text-sm text-neutral-600 dark:text-neutral-400">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-center gap-2">
                        <span className="text-green-500">✓</span> {f}
                      </li>
                    ))}
                  </ul>
                  <Button
                    className="w-full"
                    variant={plan.popular ? "default" : "outline"}
                    asChild
                  >
                    <Link href={plan.name === "Business" ? "/contact" : "/signup"}>
                      {plan.cta}
                    </Link>
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Email Capture / CTA */}
        <section className="border-t border-neutral-200 bg-indigo-50 py-24 dark:border-neutral-800 dark:bg-indigo-950">
          <div className="mx-auto max-w-2xl px-4 text-center">
            <h2 className="mb-4 text-3xl font-bold">
              Ready to start collecting feedback?
            </h2>
            <p className="mb-8 text-neutral-600 dark:text-neutral-400">
              Join thousands of product teams using SimpleFeedback to build better products.
            </p>
            <div className="mx-auto flex max-w-md flex-col gap-3 sm:flex-row">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 rounded-lg border border-neutral-300 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-neutral-700 dark:bg-neutral-900"
              />
              <Button asChild>
                <Link href="/signup">Get Started Free</Link>
              </Button>
            </div>
            <p className="mt-3 text-xs text-neutral-400">
              Free plan includes 1 project and 100 feedback items. No credit card required.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-200 py-12 dark:border-neutral-800">
        <div className="mx-auto max-w-6xl px-4">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <div className="mb-4 text-lg font-bold">SimpleFeedback</div>
              <p className="text-sm text-neutral-500">
                The simplest way to collect, organize, and act on user feedback.
              </p>
            </div>
            <div>
              <div className="mb-4 text-sm font-semibold uppercase tracking-wider text-neutral-500">
                Product
              </div>
              <div className="flex flex-col gap-2 text-sm">
                <Link href="/features" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  Features
                </Link>
                <Link href="/pricing" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  Pricing
                </Link>
                <Link href="/docs" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  Documentation
                </Link>
                <Link href="/changelog" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  Changelog
                </Link>
              </div>
            </div>
            <div>
              <div className="mb-4 text-sm font-semibold uppercase tracking-wider text-neutral-500">
                Company
              </div>
              <div className="flex flex-col gap-2 text-sm">
                <Link href="/about" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  About
                </Link>
                <Link href="/blog" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  Blog
                </Link>
                <Link href="/support" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  Support
                </Link>
                <Link href="/contact" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  Contact
                </Link>
              </div>
            </div>
            <div>
              <div className="mb-4 text-sm font-semibold uppercase tracking-wider text-neutral-500">
                Legal
              </div>
              <div className="flex flex-col gap-2 text-sm">
                <Link href="/legal/privacy" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  Privacy Policy
                </Link>
                <Link href="/legal/terms" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  Terms of Service
                </Link>
                <Link href="/legal/cookies" className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-200">
                  Cookie Policy
                </Link>
              </div>
            </div>
          </div>
          <div className="mt-12 border-t border-neutral-200 pt-8 text-center text-sm text-neutral-500 dark:border-neutral-800">
            &copy; {new Date().getFullYear()} SimpleFeedback. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
