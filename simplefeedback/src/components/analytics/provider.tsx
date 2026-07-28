"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";

const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY || "";
const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://app.posthog.com";

declare global {
  interface Window {
    posthog?: {
      init: (key: string, config: Record<string, unknown>) => void;
      capture: (event: string, properties?: Record<string, unknown>) => void;
      identify: (id: string, traits?: Record<string, unknown>) => void;
      reset: () => void;
    };
  }
}

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (!POSTHOG_KEY || typeof window === "undefined") return;

    // Load PostHog script
    const script = document.createElement("script");
    script.src = `${POSTHOG_HOST}/static/array.js`;
    script.async = true;
    script.onload = () => {
      if (window.posthog) {
        window.posthog.init(POSTHOG_KEY, {
          api_host: POSTHOG_HOST,
          person_profiles: "identified_only",
          capture_pageview: false,
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      // Cleanup
      const existing = document.querySelector(
        `script[src="${POSTHOG_HOST}/static/array.js"]`
      );
      if (existing) existing.remove();
    };
  }, []);

  // Track page views
  useEffect(() => {
    if (window.posthog && pathname) {
      const url = searchParams?.toString()
        ? `${pathname}?${searchParams.toString()}`
        : pathname;
      window.posthog.capture("$pageview", { $current_url: url });
    }
  }, [pathname, searchParams]);

  return <>{children}</>;
}
