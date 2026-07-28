"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/use-toast";

interface Props {
  hasSubscription: boolean;
  customerId: string | null;
}

export function ManageSubscription({ hasSubscription, customerId }: Props) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleManage = async () => {
    setLoading(true);
    const res = await fetch("/api/manage-subscription", { method: "POST" });
    if (res.ok) {
      const { url } = await res.json();
      if (url) window.location.href = url;
    } else {
      toast({ title: "Failed to open billing portal", variant: "destructive" });
    }
    setLoading(false);
  };

  if (!hasSubscription) return null;

  return (
    <Button variant="outline" onClick={handleManage} disabled={loading}>
      {loading ? "Loading..." : "Manage Subscription"}
    </Button>
  );
}
