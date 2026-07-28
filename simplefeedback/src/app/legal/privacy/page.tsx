import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy - SimpleFeedback",
  description: "Privacy Policy for SimpleFeedback. Learn how we collect, use, and protect your data.",
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-2 text-3xl font-bold">Privacy Policy</h1>
      <p className="mb-8 text-sm text-neutral-500">Last updated: July 26, 2026</p>

      <div className="prose prose-sm max-w-none space-y-6 dark:prose-invert">
        <h2>1. Introduction</h2>
        <p>
          SimpleFeedback ("we," "our," or "us") is committed to protecting your privacy.
          This Privacy Policy explains how we collect, use, disclose, and safeguard your
          information when you use our service.
        </p>

        <h2>2. Information We Collect</h2>
        <h3>Information You Provide</h3>
        <ul>
          <li>Account information: name, email address, and password</li>
          <li>Organization information: company name, billing address</li>
          <li>Feedback content: titles, descriptions, comments, and votes</li>
          <li>Communication preferences: notification settings</li>
        </ul>

        <h3>Information Collected Automatically</h3>
        <ul>
          <li>Usage data: pages visited, features used, time spent</li>
          <li>Device information: browser type, operating system, IP address</li>
          <li>Cookies and similar tracking technologies (see our{" "}
            <Link href="/legal/cookies" className="text-indigo-600 underline">Cookie Policy</Link>)</li>
        </ul>

        <h2>3. How We Use Your Information</h2>
        <p>We use your information to:</p>
        <ul>
          <li>Provide, maintain, and improve the Service</li>
          <li>Process transactions and send billing information</li>
          <li>Send technical notices, updates, and support messages</li>
          <li>Respond to your comments, questions, and requests</li>
          <li>Monitor and analyze usage patterns and trends</li>
          <li>Detect, investigate, and prevent fraudulent transactions</li>
        </ul>

        <h2>4. Data Sharing and Disclosure</h2>
        <p>
          We do not sell your personal information. We may share your information with:
        </p>
        <ul>
          <li>Service providers who assist in operating our platform (e.g., hosting, analytics)</li>
          <li>Legal authorities when required by law or to protect our rights</li>
          <li>Other parties with your consent or at your direction</li>
        </ul>

        <h2>5. Data Security</h2>
        <p>
          We implement appropriate technical and organizational measures to protect your
          information, including encryption at rest and in transit, access controls, and
          regular security audits.
        </p>

        <h2>6. Data Retention</h2>
        <p>
          We retain your information for as long as your account is active or as needed to
          provide the Service. You may request deletion of your data at any time.
        </p>

        <h2>7. Your Rights</h2>
        <p>You have the right to:</p>
        <ul>
          <li>Access and review your personal data</li>
          <li>Correct inaccurate or incomplete data</li>
          <li>Delete your data and account</li>
          <li>Export your data in a portable format</li>
          <li>Object to or restrict processing of your data</li>
          <li>Withdraw consent at any time</li>
        </ul>

        <h2>8. Third-Party Services</h2>
        <p>
          The Service may contain links to third-party websites. We are not responsible for
          the privacy practices of these third parties.
        </p>

        <h2>9. Children's Privacy</h2>
        <p>
          The Service is not intended for children under 13. We do not knowingly collect
          personal information from children.
        </p>

        <h2>10. International Data Transfers</h2>
        <p>
          Your information may be transferred to and processed in countries other than your
          own. We ensure appropriate safeguards are in place for such transfers.
        </p>

        <h2>11. Changes to This Policy</h2>
        <p>
          We may update this Privacy Policy from time to time. We will notify you of material
          changes via email or through the Service.
        </p>

        <h2>12. Contact</h2>
        <p>
          For questions about this Privacy Policy, contact us at{" "}
          <a href="mailto:privacy@simplefeedback.com" className="text-indigo-600 underline">
            privacy@simplefeedback.com
          </a>.
        </p>
      </div>
    </div>
  );
}
