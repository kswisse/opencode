"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/use-toast";

const statuses = [
  { value: "OPEN", label: "Open" },
  { value: "PLANNED", label: "Planned" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "COMPLETED", label: "Completed" },
  { value: "DECLINED", label: "Declined" },
];

export function FeedbackStatusActions({
  feedbackId,
  currentStatus,
}: {
  feedbackId: string;
  currentStatus: string;
}) {
  const [loading, setLoading] = useState<string | null>(null);
  const router = useRouter();

  const updateStatus = async (status: string) => {
    setLoading(status);
    const res = await fetch(`/api/feedback/${feedbackId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });

    if (res.ok) {
      toast({ title: "Status updated" });
      router.refresh();
    } else {
      toast({ title: "Failed to update status", variant: "destructive" });
    }
    setLoading(null);
  };

  return (
    <div className="flex flex-wrap gap-2">
      {statuses.map((s) => (
        <Button
          key={s.value}
          size="sm"
          variant={currentStatus === s.value ? "default" : "outline"}
          disabled={loading === s.value}
          onClick={() => updateStatus(s.value)}
        >
          {s.label}
        </Button>
      ))}
    </div>
  );
}
