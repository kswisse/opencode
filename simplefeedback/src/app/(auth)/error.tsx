"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AuthError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Authentication Error</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-neutral-500">
            Something went wrong. Please try signing in again.
          </p>
          {process.env.NODE_ENV === "development" && (
            <pre className="rounded-md bg-neutral-100 p-3 text-xs text-red-600 dark:bg-neutral-800 dark:text-red-400 overflow-auto">
              {error.message}
            </pre>
          )}
          <div className="flex gap-2">
            <Button onClick={reset}>Try again</Button>
            <Button variant="outline" onClick={() => window.location.href = "/login"}>
              Go to login
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
