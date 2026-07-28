"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "@/components/ui/use-toast";
import { formatRelativeTime } from "@/lib/utils";
import { Shield, Users, Lightbulb, FolderKanban } from "lucide-react";

type OrgWithCounts = {
  id: string;
  name: string;
  slug: string;
  createdAt: Date;
  _count: {
    users: number;
    feedback: number;
    projects: number;
  };
  subscription: {
    plan: string;
    status: string | null;
  } | null;
};

interface AdminClientProps {
  organizations: OrgWithCounts[];
}

export function AdminClient({ organizations }: AdminClientProps) {
  const router = useRouter();
  const [selectedOrg, setSelectedOrg] = useState<OrgWithCounts | null>(null);
  const [planOverride, setPlanOverride] = useState<string>("FREE");
  const [isOverriding, setIsOverriding] = useState(false);

  const handleOverridePlan = async () => {
    if (!selectedOrg) return;
    setIsOverriding(true);

    try {
      const res = await fetch("/api/admin", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "override_plan",
          organizationId: selectedOrg.id,
          plan: planOverride,
        }),
      });

      if (!res.ok) throw new Error("Failed to override plan");
      toast({ title: "Plan overridden", description: `${selectedOrg.name} is now on ${planOverride} plan.` });
      setSelectedOrg(null);
      router.refresh();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to override plan",
        variant: "destructive",
      });
    } finally {
      setIsOverriding(false);
    }
  };

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Organization</TableHead>
            <TableHead>Plan</TableHead>
            <TableHead>Members</TableHead>
            <TableHead>Projects</TableHead>
            <TableHead>Feedback</TableHead>
            <TableHead>Created</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {organizations.map((org) => (
            <TableRow key={org.id}>
              <TableCell>
                <div>
                  <p className="font-medium text-sm">{org.name}</p>
                  <code className="text-xs text-neutral-500">{org.slug}</code>
                </div>
              </TableCell>
              <TableCell>
                <Badge
                  variant={
                    org.subscription?.plan === "BUSINESS"
                      ? "default"
                      : org.subscription?.plan === "PRO"
                      ? "secondary"
                      : "outline"
                  }
                >
                  {org.subscription?.plan || "FREE"}
                </Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-1 text-sm">
                  <Users className="h-3 w-3 text-neutral-400" />
                  {org._count.users}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-1 text-sm">
                  <FolderKanban className="h-3 w-3 text-neutral-400" />
                  {org._count.projects}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-1 text-sm">
                  <Lightbulb className="h-3 w-3 text-neutral-400" />
                  {org._count.feedback}
                </div>
              </TableCell>
              <TableCell className="text-xs text-neutral-500">
                {formatRelativeTime(org.createdAt)}
              </TableCell>
              <TableCell>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSelectedOrg(org);
                    setPlanOverride(org.subscription?.plan || "FREE");
                  }}
                >
                  <Shield className="h-3 w-3 mr-1" />
                  Override Plan
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Plan Override Dialog */}
      <Dialog open={!!selectedOrg} onOpenChange={(open) => !open && setSelectedOrg(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Override Plan</DialogTitle>
            <DialogDescription>
              Change the subscription plan for <strong>{selectedOrg?.name}</strong>.
              This bypasses Stripe billing.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <label className="text-sm font-medium mb-2 block">New Plan</label>
            <Select value={planOverride} onValueChange={setPlanOverride}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="FREE">Free</SelectItem>
                <SelectItem value="PRO">Pro</SelectItem>
                <SelectItem value="BUSINESS">Business</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedOrg(null)}>
              Cancel
            </Button>
            <Button onClick={handleOverridePlan} disabled={isOverriding}>
              {isOverriding ? "Saving..." : "Override Plan"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
