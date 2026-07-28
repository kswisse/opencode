import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";
import { AnalyticsProvider } from "@/components/analytics/provider";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const baseUrl = process.env.NEXT_PUBLIC_APP_URL || "https://simplefeedback.com";

export const metadata: Metadata = {
  title: {
    default: "SimpleFeedback - Collect and Manage User Feedback",
    template: "%s - SimpleFeedback",
  },
  description:
    "The simplest way to collect, organize, and act on user feedback. Public boards, roadmaps, changelogs, and AI-powered insights.",
  metadataBase: new URL(baseUrl),
  openGraph: {
    title: "SimpleFeedback - Collect and Manage User Feedback",
    description:
      "The simplest way to collect, organize, and act on user feedback. Public boards, roadmaps, changelogs, and AI-powered insights.",
    url: baseUrl,
    siteName: "SimpleFeedback",
    locale: "en_US",
    type: "website",
    images: [
      {
        url: "/og?title=SimpleFeedback&description=Collect%2C%20organize%2C%20and%20act%20on%20user%20feedback",
        width: 1200,
        height: 630,
        alt: "SimpleFeedback",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "SimpleFeedback - Collect and Manage User Feedback",
    description:
      "The simplest way to collect, organize, and act on user feedback. Public boards, roadmaps, changelogs, and AI-powered insights.",
    images: [
      "/og?title=SimpleFeedback&description=Collect%2C%20organize%2C%20and%20act%20on%20user%20feedback",
    ],
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: "/icon.svg",
    apple: "/apple-icon.png",
  },
  manifest: "/manifest.webmanifest",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-md focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-neutral-900 focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          Skip to main content
        </a>
        <div id="main-content" className="flex-1 flex flex-col">
          <Suspense fallback={null}>
            <AnalyticsProvider>{children}</AnalyticsProvider>
          </Suspense>
        </div>
      </body>
    </html>
  );
}
