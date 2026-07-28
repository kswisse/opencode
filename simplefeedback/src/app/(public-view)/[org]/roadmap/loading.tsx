import { Skeleton } from "@/components/ui/skeleton";

export default function PublicRoadmapLoading() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <Skeleton className="mx-auto h-10 w-72" />
        <Skeleton className="mx-auto mt-2 h-4 w-80" />
      </div>
      <div className="grid gap-6 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-lg border p-6">
            <div className="flex items-center gap-2">
              <Skeleton className="h-2 w-2 rounded-full" />
              <Skeleton className="h-5 w-28" />
            </div>
            <div className="mt-4 space-y-3">
              {Array.from({ length: 3 }).map((_, j) => (
                <div key={j} className="rounded-lg border p-3">
                  <Skeleton className="h-4 w-36" />
                  <Skeleton className="mt-1 h-3 w-12" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
