import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Blog - SimpleFeedback",
  description:
    "Product management insights, feedback best practices, and tips for building customer-centric products.",
  openGraph: {
    title: "Blog - SimpleFeedback",
    description:
      "Product management insights, feedback best practices, and tips for building customer-centric products.",
  },
};

export default function BlogLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-neutral-200 dark:border-neutral-800">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="text-lg font-bold tracking-tight">
            SimpleFeedback
          </Link>
          <nav className="flex items-center gap-4">
            <Link
              href="/blog"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              Blog
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-neutral-200 py-8 dark:border-neutral-800">
        <div className="mx-auto max-w-6xl px-4 text-center text-sm text-neutral-500">
          &copy; {new Date().getFullYear()} SimpleFeedback. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
