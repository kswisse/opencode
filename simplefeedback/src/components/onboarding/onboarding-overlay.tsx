"use client";

import { useState, useEffect } from "react";
import { X, ChevronRight, ChevronLeft, Check, Lightbulb, FolderKanban, ListTodo, RoadIcon, Newspaper, Puzzle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { OnboardingStep } from "./onboarding-provider";

interface OnboardingOverlayProps {
  currentStep: number;
  totalSteps: number;
  steps: readonly OnboardingStep[];
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
  onComplete: () => void;
  onGoTo: (step: number) => void;
}

const stepContent: Record<OnboardingStep, {
  title: string;
  description: string;
  icon: React.ElementType;
  tips: string[];
}> = {
  welcome: {
    title: "Welcome to SimpleFeedback!",
    description: "Let's get you set up in just a few steps. We'll help you start collecting and managing feedback like a pro.",
    icon: Lightbulb,
    tips: [
      "Collect feedback from multiple channels",
      "Prioritize with AI-powered insights",
      "Keep users informed with changelogs",
    ],
  },
  "create-project": {
    title: "Create Your First Project",
    description: "Projects help you organize feedback by product, feature, or team. Start by creating your first project.",
    icon: FolderKanban,
    tips: [
      'Click "New Project" in the sidebar',
      "Give it a clear name and description",
      "You can always add more projects later",
    ],
  },
  "view-feedback": {
    title: "View & Manage Feedback",
    description: "All feedback from your users appears here. You can filter, search, and update status as you work through items.",
    icon: ListTodo,
    tips: [
      "Use statuses to track progress (Open → Planned → In Progress → Completed)",
      "Set priority levels to focus on what matters",
      "AI will automatically detect duplicates and score priority",
    ],
  },
  roadmap: {
    title: "Share Your Roadmap",
    description: "Let users see what you're working on and what's coming next. Transparency builds trust and reduces duplicate requests.",
    icon: RoadIcon,
    tips: [
      "Organize feedback into your product roadmap",
      "Users can see planned and in-progress items",
      "Update statuses to show progress automatically",
    ],
  },
  changelogs: {
    title: "Announce Changes with Changelogs",
    description: "Keep users informed about what's changed, fixed, or improved. Share updates via your public changelog page.",
    icon: Newspaper,
    tips: [
      "AI can generate release notes from completed feedback",
      "Publish changelogs to your public page",
      "Share updates via email to subscribed users",
    ],
  },
  "widget-integration": {
    title: "Embed the Feedback Widget",
    description: "Add the feedback widget to your website or app so users can submit feedback without leaving your product.",
    icon: Puzzle,
    tips: [
      'Copy the widget script from Settings → Widget',
      "Add it to your website's code",
      "Customize the look and feel to match your brand",
    ],
  },
};

export function OnboardingOverlay({
  currentStep,
  totalSteps,
  steps,
  onNext,
  onBack,
  onSkip,
  onComplete,
  onGoTo,
}: OnboardingOverlayProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const stepName = steps[currentStep];
  const content = stepContent[stepName];
  const isLastStep = currentStep === totalSteps - 1;
  const progress = ((currentStep + 1) / totalSteps) * 100;
  const StepIcon = content.icon;

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm transition-opacity duration-300",
        visible ? "opacity-100" : "opacity-0"
      )}
    >
      <div
        className={cn(
          "relative w-full max-w-lg mx-4 transition-all duration-300",
          visible ? "scale-100 translate-y-0" : "scale-95 translate-y-4"
        )}
      >
        <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="relative p-6 pb-0">
            <button
              onClick={onSkip}
              className="absolute right-4 top-4 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
            >
              <X className="h-5 w-5" />
              <span className="sr-only">Skip tour</span>
            </button>

            {/* Progress bar */}
            <div className="w-full h-1.5 bg-neutral-100 dark:bg-neutral-800 rounded-full mb-6 overflow-hidden">
              <div
                className="h-full bg-neutral-900 dark:bg-neutral-200 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>

            {/* Step indicator dots */}
            <div className="flex items-center justify-center mb-4">
              <div className="flex items-center gap-1.5">
                {steps.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => onGoTo(index)}
                    className={cn(
                      "rounded-full transition-all duration-300",
                      index === currentStep
                        ? "bg-neutral-900 dark:bg-neutral-200 w-6 h-2"
                        : index < currentStep
                        ? "bg-neutral-400 dark:bg-neutral-500 w-2 h-2"
                        : "bg-neutral-200 dark:bg-neutral-700 w-2 h-2"
                    )}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 pt-4">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-neutral-100 dark:bg-neutral-800 mb-4">
                <StepIcon className="h-8 w-8 text-neutral-700 dark:text-neutral-300" />
              </div>

              <h2 className="text-xl font-bold mb-2 text-neutral-900 dark:text-neutral-100">
                {content.title}
              </h2>
              <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-6 leading-relaxed">
                {content.description}
              </p>

              <div className="text-left bg-neutral-50 dark:bg-neutral-800/50 rounded-xl p-4 space-y-2 mb-6">
                <p className="text-xs font-semibold text-neutral-400 dark:text-neutral-500 uppercase tracking-wider">
                  Tips
                </p>
                {content.tips.map((tip, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm text-neutral-600 dark:text-neutral-300">
                    <Check className="h-4 w-4 mt-0.5 text-green-500 shrink-0" />
                    <span>{tip}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 pt-0">
            <Button
              variant="ghost"
              onClick={onSkip}
              className="text-sm text-neutral-400"
            >
              Skip tour
            </Button>

            <div className="flex items-center gap-2">
              {currentStep > 0 && (
                <Button variant="outline" onClick={onBack} size="sm">
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Back
                </Button>
              )}

              {isLastStep ? (
                <Button onClick={onComplete} size="sm">
                  <Check className="h-4 w-4 mr-1" />
                  Get Started
                </Button>
              ) : (
                <Button onClick={onNext} size="sm">
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
