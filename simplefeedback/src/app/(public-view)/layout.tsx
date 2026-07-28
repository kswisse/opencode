import Link from "next/link";
import { Toaster } from "@/components/ui/toaster";
import { ThemeToggle } from "@/components/theme/theme-toggle";

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="border-b border-neutral-200 dark:border-neutral-800">
        <div className="mx-auto flex h-14 max-w-4xl items-center justify-between px-4">
          <Link href="/" className="text-lg font-bold">
            SimpleFeedback
          </Link>
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-8">{children}</main>
      <Toaster />
    </>
  );
}
