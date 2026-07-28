"use client";

import { useEffect, useState, useCallback } from "react";

export interface Shortcut {
  keys: string[];
  description: string;
  action: () => void;
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  const [buffer, setBuffer] = useState<string[]>([]);
  const [showHelp, setShowHelp] = useState(false);

  const clearBuffer = useCallback(() => {
    setBuffer([]);
  }, []);

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        // Allow Escape in inputs
        if (e.key === "Escape") {
          setShowHelp(false);
        }
        return;
      }

      // Show help dialog with ?
      if (e.key === "?" && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        setShowHelp((prev) => !prev);
        return;
      }

      // Handle Escape to close help
      if (e.key === "Escape") {
        setShowHelp(false);
        return;
      }

      // Single key shortcuts
      if (e.key === "n" && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        const nShortcut = shortcuts.find((s) => s.keys.length === 1 && s.keys[0] === "n");
        if (nShortcut) {
          nShortcut.action();
        }
        return;
      }

      // Buffer-based shortcuts (g + key)
      if (e.key === "g" && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        setBuffer(["g"]);
        timeout = setTimeout(clearBuffer, 1000);
        return;
      }

      if (buffer.includes("g")) {
        const combo = `g+${e.key}`;
        const shortcut = shortcuts.find(
          (s) => s.keys.length === 2 && s.keys[0] === "g" && s.keys[1] === e.key
        );
        if (shortcut) {
          e.preventDefault();
          shortcut.action();
        }
        clearBuffer();
        clearTimeout(timeout);
        return;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      clearTimeout(timeout);
    };
  }, [shortcuts, buffer, clearBuffer]);

  return { showHelp, setShowHelp };
}
