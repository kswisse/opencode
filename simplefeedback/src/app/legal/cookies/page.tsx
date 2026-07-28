import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Cookie Policy - SimpleFeedback",
  description: "Cookie Policy for SimpleFeedback. Learn about how we use cookies and similar technologies.",
};

export default function CookiesPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-2 text-3xl font-bold">Cookie Policy</h1>
      <p className="mb-8 text-sm text-neutral-500">Last updated: July 26, 2026</p>

      <div className="prose prose-sm max-w-none space-y-6 dark:prose-invert">
        <h2>1. What Are Cookies</h2>
        <p>
          Cookies are small text files that are stored on your device when you visit a website.
          They help websites remember your preferences, understand how you use the site, and
          improve your experience.
        </p>

        <h2>2. How We Use Cookies</h2>
        <p>We use cookies for the following purposes:</p>

        <h3>Essential Cookies</h3>
        <p>
          These cookies are necessary for the Service to function properly. They enable core
          functionality such as authentication, session management, and security.
        </p>
        <ul>
          <li>Session cookies — maintain your login state</li>
          <li>CSRF tokens — protect against cross-site request forgery</li>
          <li>Rate limiting — prevent abuse of the Service</li>
        </ul>

        <h3>Analytics Cookies</h3>
        <p>
          These cookies help us understand how users interact with the Service, allowing us
          to improve features and user experience.
        </p>
        <ul>
          <li>Page view tracking</li>
          <li>Feature usage analytics</li>
          <li>Performance monitoring</li>
        </ul>

        <h3>Preference Cookies</h3>
        <p>
          These cookies remember your preferences and settings to provide a personalized experience.
        </p>
        <ul>
          <li>Theme preference (light/dark mode)</li>
          <li>Language preference</li>
          <li>Notification settings</li>
        </ul>

        <h2>3. Types of Cookies We Use</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="pb-2 pr-4 text-left font-semibold">Cookie</th>
              <th className="pb-2 pr-4 text-left font-semibold">Type</th>
              <th className="pb-2 pr-4 text-left font-semibold">Duration</th>
              <th className="pb-2 text-left font-semibold">Purpose</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            <tr>
              <td className="py-2 pr-4 font-mono text-xs">sb-session</td>
              <td className="py-2 pr-4">Essential</td>
              <td className="py-2 pr-4">Session</td>
              <td className="py-2">Authentication</td>
            </tr>
            <tr>
              <td className="py-2 pr-4 font-mono text-xs">sf-prefs</td>
              <td className="py-2 pr-4">Preference</td>
              <td className="py-2 pr-4">1 year</td>
              <td className="py-2">User preferences</td>
            </tr>
            <tr>
              <td className="py-2 pr-4 font-mono text-xs">_ph</td>
              <td className="py-2 pr-4">Analytics</td>
              <td className="py-2 pr-4">1 year</td>
              <td className="py-2">Usage analytics</td>
            </tr>
          </tbody>
        </table>

        <h2>4. Third-Party Cookies</h2>
        <p>
          We use third-party services that may set their own cookies:
        </p>
        <ul>
          <li>Stripe — payment processing (see Stripe's privacy policy)</li>
          <li>PostHog — product analytics (see PostHog's privacy policy)</li>
          <li>Supabase — authentication and database services</li>
        </ul>

        <h2>5. Managing Cookies</h2>
        <p>
          Most web browsers allow you to control cookies through their settings. You can:
        </p>
        <ul>
          <li>Delete all cookies from your browser</li>
          <li>Block third-party cookies</li>
          <li>Block all cookies (this may affect Service functionality)</li>
          <li>Set preferences for specific websites</li>
        </ul>
        <p>
          For more information on managing cookies, visit{" "}
          <a href="https://www.aboutcookies.org" className="text-indigo-600 underline" target="_blank" rel="noopener noreferrer">
            aboutcookies.org
          </a>.
        </p>

        <h2>6. Updates to This Policy</h2>
        <p>
          We may update this Cookie Policy from time to time. Changes will be posted on this
          page with an updated revision date.
        </p>

        <h2>7. Contact</h2>
        <p>
          For questions about our use of cookies, contact us at{" "}
          <a href="mailto:privacy@simplefeedback.com" className="text-indigo-600 underline">
            privacy@simplefeedback.com
          </a>.
        </p>
      </div>
    </div>
  );
}
