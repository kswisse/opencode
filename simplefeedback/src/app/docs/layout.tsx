import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Documentation - SimpleFeedback",
  description:
    "Learn how to set up and use SimpleFeedback. Guides for installation, API reference, integrations, and more.",
};

const sidebarLinks = [
  { title: "Getting Started", href: "/docs" },
  { title: "Installation", href: "/docs/installation" },
  { title: "API Reference", href: "/docs/api" },
  { title: "Integrations", href: "/docs/integrations" },
];

export default function DocsLayout({
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
              href="/docs"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              Docs
            </Link>
            <Link
              href="/support"
              className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400"
            >
              Support
            </Link>
          </nav>
        </div>
      </header>
      <div className="mx-auto flex w-full max-w-6xl flex-1 px-4">
        <aside className="hidden w-56 shrink-0 border-r border-neutral-200 py-8 pr-6 dark:border-neutral-800 lg:block">
          <nav className="space-y-1">
            {sidebarLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="block rounded-md px-3 py-2 text-sm text-neutral-600 transition-colors hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-200"
              >
                {link.title}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="min-w-0 flex-1 py-8 pl-0 lg:pl-8">
          <div className="prose prose-sm max-w-none dark:prose-invert">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
