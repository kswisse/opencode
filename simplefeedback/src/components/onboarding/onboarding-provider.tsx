"use client";

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
import { OnboardingOverlay } from "./onboarding-overlay";

type OnboardingContextType = {
  isActive: boolean;
  currentStep: number;
  totalSteps: number;
  start: () => void;
  next: () => void;
  back: () => void;
  skip: () => void;
  complete: () => void;
  goTo: (step: number) => void;
};

const OnboardingContext = createContext<OnboardingContextType | null>(null);

export function useOnboarding() {
  const ctx = useContext(OnboardingContext);
  if (!ctx) throw new Error("useOnboarding must be used within OnboardingProvider");
  return ctx;
}

const ONBOARDING_STEPS = [
  "welcome",
  "create-project",
  "view-feedback",
  "roadmap",
  "changelogs",
  "widget-integration",
] as const;

export type OnboardingStep = (typeof ONBOARDING_STEPS)[number];

export function OnboardingProvider({
  children,
  defaultCompleted = false,
}: {
  children: ReactNode;
  defaultCompleted?: boolean;
}) {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [hasCompleted, setHasCompleted] = useState(defaultCompleted);

  useEffect(() => {
    const stored = localStorage.getItem("sf-onboarding-completed");
    if (stored === "true") {
      setHasCompleted(true);
    }
  }, []);

  const start = useCallback(() => {
    if (!hasCompleted) {
      setIsActive(true);
      setCurrentStep(0);
    }
  }, [hasCompleted]);

  const next = useCallback(() => {
    setCurrentStep((prev) => Math.min(prev + 1, ONBOARDING_STEPS.length - 1));
  }, []);

  const back = useCallback(() => {
    setCurrentStep((prev) => Math.max(prev - 1, 0));
  }, []);

  const goTo = useCallback((step: number) => {
    setCurrentStep(Math.max(0, Math.min(step, ONBOARDING_STEPS.length - 1)));
  }, []);

  const skip = useCallback(() => {
    setIsActive(false);
    localStorage.setItem("sf-onboarding-completed", "true");
    setHasCompleted(true);
  }, []);

  const complete = useCallback(() => {
    setIsActive(false);
    localStorage.setItem("sf-onboarding-completed", "true");
    setHasCompleted(true);
    // Also mark in the backend
    fetch("/api/auth/complete-onboarding", { method: "POST" }).catch(() => {});
  }, []);

  return (
    <OnboardingContext.Provider
      value={{
        isActive,
        currentStep,
        totalSteps: ONBOARDING_STEPS.length,
        start,
        next,
        back,
        skip,
        complete,
        goTo,
      }}
    >
      {children}
      {isActive && (
        <OnboardingOverlay
          currentStep={currentStep}
          totalSteps={ONBOARDING_STEPS.length}
          steps={ONBOARDING_STEPS}
          onNext={next}
          onBack={back}
          onSkip={skip}
          onComplete={complete}
          onGoTo={goTo}
        />
      )}
    </OnboardingContext.Provider>
  );
}
