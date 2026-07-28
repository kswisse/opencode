"use client";

import { useRouter } from "next/navigation";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";
import { KeyboardShortcutsHelp } from "@/components/dashboard/keyboard-shortcuts-help";

export function DashboardShortcuts() {
  const router = useRouter();

  const shortcuts = [
    { keys: ["g", "d"], description: "Go to Dashboard", action: () => router.push("/dashboard") },
    { keys: ["g", "f"], description: "Go to Feedback", action: () => router.push("/dashboard/feedback") },
    { keys: ["g", "r"], description: "Go to Roadmap", action: () => router.push("/dashboard/roadmap") },
    { keys: ["g", "c"], description: "Go to Changelogs", action: () => router.push("/dashboard/changelogs") },
    { keys: ["g", "s"], description: "Go to Settings", action: () => router.push("/dashboard/settings") },
    { keys: ["n"], description: "Create new item", action: () => {
      // Context-dependent - default to new project for now
      router.push("/dashboard/projects/new");
    }},
  ];

  const { showHelp, setShowHelp } = useKeyboardShortcuts(shortcuts);

  return (
    <KeyboardShortcutsHelp open={showHelp} onOpenChange={setShowHelp} />
  );
}
