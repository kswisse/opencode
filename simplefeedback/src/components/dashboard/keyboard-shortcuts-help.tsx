"use client";

import { useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface KeyboardShortcut {
  keys: string[];
  description: string;
}

const shortcuts: KeyboardShortcut[] = [
  { keys: ["g", "d"], description: "Go to Dashboard" },
  { keys: ["g", "f"], description: "Go to Feedback" },
  { keys: ["g", "r"], description: "Go to Roadmap" },
  { keys: ["g", "c"], description: "Go to Changelogs" },
  { keys: ["g", "s"], description: "Go to Settings" },
  { keys: ["n"], description: "Create new item" },
  { keys: ["?"], description: "Toggle this help dialog" },
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function KeyboardShortcutsHelp({ open, onOpenChange }: Props) {
  // Close on Escape is handled by Dialog

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Use these shortcuts to navigate quickly
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {shortcuts.map((shortcut) => (
            <div
              key={shortcut.keys.join("+")}
              className="flex items-center justify-between"
            >
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                {shortcut.description}
              </span>
              <div className="flex items-center gap-1">
                {shortcut.keys.map((key, i) => (
                  <span key={key}>
                    <kbd className="inline-flex h-7 min-w-[1.75rem] items-center justify-center rounded-md border border-neutral-200 bg-neutral-50 px-1.5 text-xs font-medium text-neutral-600 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400">
                      {key === "g" ? "G" : key === "n" ? "N" : key}
                    </kbd>
                    {i < shortcut.keys.length - 1 && (
                      <span className="mx-1 text-xs text-neutral-400">then</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
