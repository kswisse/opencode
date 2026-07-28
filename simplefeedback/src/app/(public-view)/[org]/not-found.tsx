import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Building2 } from "lucide-react";

export default function OrgNotFound() {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center space-y-4">
      <div className="rounded-full bg-neutral-100 p-3 dark:bg-neutral-800">
        <Building2 className="h-6 w-6 text-neutral-600 dark:text-neutral-400" />
      </div>
      <div className="text-center">
        <h2 className="text-lg font-semibold">Organization not found</h2>
        <p className="mt-1 text-sm text-neutral-500">
          This organization does not exist or has no public page.
        </p>
      </div>
      <Button variant="outline" asChild>
        <Link href="/">Go home</Link>
      </Button>
    </div>
  );
}
