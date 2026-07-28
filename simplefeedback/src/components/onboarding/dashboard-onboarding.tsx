"use client";

import { useEffect } from "react";
import { useOnboarding } from "./onboarding-provider";

export function DashboardOnboarding({
  onboardingCompleted,
}: {
  onboardingCompleted: boolean;
}) {
  const { start } = useOnboarding();

  useEffect(() => {
    if (!onboardingCompleted) {
      const timer = setTimeout(() => {
        start();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [onboardingCompleted, start]);

  return null;
}
