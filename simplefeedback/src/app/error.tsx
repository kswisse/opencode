"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-neutral-900">Something went wrong</h1>
        <p className="mt-2 text-neutral-500">
          An unexpected error occurred. Our team has been notified.
        </p>
        {process.env.NODE_ENV === "development" && (
          <pre className="mt-4 overflow-auto rounded-lg bg-neutral-100 p-4 text-left text-sm text-neutral-700">
            {error.message}
          </pre>
        )}
        <button
          onClick={reset}
          className="mt-6 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
