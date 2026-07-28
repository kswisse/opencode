"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/components/ui/use-toast";

interface Props {
  organization: { name: string; slug: string };
  user: { name: string | null; email: string };
}

export function SettingsForm({ organization, user }: Props) {
  const [orgName, setOrgName] = useState(organization.name);
  const [name, setName] = useState(user.name || "");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const res = await fetch("/api/organization", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ orgName, name }),
    });

    if (res.ok) {
      toast({ title: "Settings updated" });
      router.refresh();
    } else {
      toast({ title: "Failed to update settings", variant: "destructive" });
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Your Name</Label>
        <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" value={user.email} disabled />
      </div>
      <div className="space-y-2">
        <Label htmlFor="orgName">Organization Name</Label>
        <Input id="orgName" value={orgName} onChange={(e) => setOrgName(e.target.value)} />
      </div>
      <div className="space-y-2">
        <Label>Organization Slug</Label>
        <Input value={organization.slug} disabled />
        <p className="text-xs text-neutral-500">Public board URL: /{organization.slug}/feedback</p>
      </div>
      <Button type="submit" disabled={loading}>
        {loading ? "Saving..." : "Save Changes"}
      </Button>
    </form>
  );
}
