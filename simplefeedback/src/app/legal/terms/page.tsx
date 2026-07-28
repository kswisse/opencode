import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Service - SimpleFeedback",
  description: "Terms of Service for using SimpleFeedback.",
};

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-2 text-3xl font-bold">Terms of Service</h1>
      <p className="mb-8 text-sm text-neutral-500">Last updated: July 26, 2026</p>

      <div className="prose prose-sm max-w-none space-y-6 dark:prose-invert">
        <h2>1. Acceptance of Terms</h2>
        <p>
          By accessing or using SimpleFeedback ("the Service"), you agree to be bound by these
          Terms of Service. If you do not agree, do not use the Service.
        </p>

        <h2>2. Description of Service</h2>
        <p>
          SimpleFeedback provides a feedback management platform that allows organizations to
          collect, organize, and act on user feedback. The Service includes public feedback
          boards, roadmaps, changelogs, AI-powered analysis, and related features.
        </p>

        <h2>3. User Accounts</h2>
        <p>
          You are responsible for maintaining the confidentiality of your account credentials
          and for all activities that occur under your account. You must notify us immediately
          of any unauthorized use of your account.
        </p>

        <h2>4. Acceptable Use</h2>
        <p>You agree not to:</p>
        <ul>
          <li>Use the Service for any illegal purpose</li>
          <li>Upload or transmit viruses, malware, or harmful code</li>
          <li>Attempt to gain unauthorized access to the Service or its systems</li>
          <li>Interfere with or disrupt the Service</li>
          <li>Use the Service to send unsolicited communications (spam)</li>
          <li>Submit feedback containing hate speech, harassment, or abusive content</li>
        </ul>

        <h2>5. Intellectual Property</h2>
        <p>
          The Service and its original content, features, and functionality are owned by
          SimpleFeedback and are protected by intellectual property laws. You retain ownership
          of any content you submit through the Service.
        </p>

        <h2>6. Payment and Billing</h2>
        <p>
          Paid plans are billed monthly or annually in advance. You may cancel at any time,
          and access will continue until the end of your billing period. Refunds are
          provided per our refund policy.
        </p>

        <h2>7. Data Privacy</h2>
        <p>
          Our collection and use of personal data is governed by our{" "}
          <Link href="/legal/privacy" className="text-indigo-600 underline">Privacy Policy</Link>.
          You are responsible for ensuring your use of the Service complies with applicable
          data protection laws.
        </p>

        <h2>8. Limitation of Liability</h2>
        <p>
          SimpleFeedback shall not be liable for any indirect, incidental, special,
          consequential, or punitive damages arising from your use of the Service.
        </p>

        <h2>9. Termination</h2>
        <p>
          We may terminate or suspend your account at any time for violation of these terms.
          Upon termination, your right to use the Service immediately ceases.
        </p>

        <h2>10. Changes to Terms</h2>
        <p>
          We reserve the right to modify these terms at any time. We will notify users of
          material changes via email or through the Service.
        </p>

        <h2>11. Governing Law</h2>
        <p>
          These terms shall be governed by the laws of the State of California, without
          regard to its conflict of law provisions.
        </p>

        <h2>12. Contact</h2>
        <p>
          For questions about these terms, contact us at{" "}
          <a href="mailto:legal@simplefeedback.com" className="text-indigo-600 underline">
            legal@simplefeedback.com
          </a>.
        </p>
      </div>
    </div>
  );
}
