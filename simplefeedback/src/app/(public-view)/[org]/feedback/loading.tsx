import { Skeleton } from "@/components/ui/skeleton";

export default function PublicFeedbackLoading() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <Skeleton className="mx-auto h-10 w-64" />
        <Skeleton className="mx-auto mt-2 h-4 w-80" />
        <Skeleton className="mx-auto mt-4 h-10 w-40" />
      </div>
      <div className="flex flex-wrap gap-3">
        <Skeleton className="h-10 flex-1" />
        <Skeleton className="h-10 w-36" />
        <Skeleton className="h-10 w-40" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-start gap-4 rounded-lg border p-4">
            <div className="flex flex-col items-center gap-1 pt-1">
              <Skeleton className="h-4 w-4" />
              <Skeleton className="h-4 w-6" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
              <Skeleton className="mt-2 h-4 w-full max-w-lg" />
              <div className="mt-2 flex items-center gap-3">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-12" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
