"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
import { Copy, Eye, EyeOff, Plus, Trash2, Key, CheckCircle2, XCircle } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

type ApiKeyItem = {
  id: string;
  name: string;
  prefix: string;
  active: boolean;
  lastUsedAt: Date | null;
  expiresAt: Date | null;
  createdAt: Date;
};

interface ApiKeysClientProps {
  apiKeys: ApiKeyItem[];
  hasAccess: boolean;
  isAdmin: boolean;
}

export function ApiKeysClient({ apiKeys, hasAccess, isAdmin }: ApiKeysClientProps) {
  const router = useRouter();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyExpiry, setNewKeyExpiry] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [showFullKey, setShowFullKey] = useState<string | null>(null);
  const [deletingKey, setDeletingKey] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!newKeyName) return;
    setIsCreating(true);

    try {
      const res = await fetch("/api/api-keys", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newKeyName,
          expiresInDays: newKeyExpiry ? parseInt(newKeyExpiry) : null,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to create API key");
      }

      const data = await res.json();
      setCreatedKey(data.key);
      toast({
        title: "API Key Created",
        description: "Make sure to copy the key now. You won't be able to see it again.",
      });
      setNewKeyName("");
      setNewKeyExpiry("");
      router.refresh();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create API key",
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`/api/api-keys?id=${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete API key");
      toast({ title: "API Key deleted" });
      setDeletingKey(null);
      router.refresh();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete API key",
        variant: "destructive",
      });
    }
  };

  const handleToggleActive = async (id: string, currentActive: boolean) => {
    try {
      const res = await fetch("/api/api-keys", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, active: !currentActive }),
      });
      if (!res.ok) throw new Error("Failed to update API key");
      router.refresh();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update API key",
        variant: "destructive",
      });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard" });
  };

  if (!hasAccess) {
    return (
      <div className="text-center py-12">
        <Key className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Upgrade to Pro</h3>
        <p className="text-sm text-neutral-500 mb-4">
          API access is available on Pro and Business plans.
        </p>
        <a href="/dashboard/billing">
          <Button>Upgrade Now</Button>
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button
          size="sm"
          onClick={() => setShowCreateDialog(true)}
          disabled={!isAdmin}
        >
          <Plus className="h-4 w-4 mr-1" />
          Create API Key
        </Button>
      </div>

      {apiKeys.length === 0 ? (
        <div className="text-center py-8 text-sm text-neutral-500">
          No API keys created yet.
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Key</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Last Used</TableHead>
              <TableHead>Expires</TableHead>
              <TableHead>Created</TableHead>
              {isAdmin && <TableHead className="w-[80px]">Actions</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {apiKeys.map((key) => (
              <TableRow key={key.id}>
                <TableCell className="font-medium">{key.name}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <code className="text-xs bg-neutral-100 dark:bg-neutral-800 px-2 py-1 rounded">
                      {key.prefix}...
                    </code>
                    <button
                      onClick={() => setShowFullKey(showFullKey === key.id ? null : key.id)}
                      className="text-neutral-400 hover:text-neutral-600"
                    >
                      {showFullKey === key.id ? (
                        <EyeOff className="h-3 w-3" />
                      ) : (
                        <Eye className="h-3 w-3" />
                      )}
                    </button>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={key.active ? "default" : "secondary"}>
                    {key.active ? "Active" : "Disabled"}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs text-neutral-500">
                  {key.lastUsedAt ? formatRelativeTime(key.lastUsedAt) : "Never"}
                </TableCell>
                <TableCell className="text-xs text-neutral-500">
                  {key.expiresAt
                    ? new Date(key.expiresAt).toLocaleDateString()
                    : "No expiry"}
                </TableCell>
                <TableCell className="text-xs text-neutral-500">
                  {new Date(key.createdAt).toLocaleDateString()}
                </TableCell>
                {isAdmin && (
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleToggleActive(key.id, key.active)}
                        className="text-neutral-400 hover:text-neutral-600 p-1"
                        title={key.active ? "Deactivate" : "Activate"}
                      >
                        {key.active ? (
                          <XCircle className="h-4 w-4" />
                        ) : (
                          <CheckCircle2 className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        onClick={() => setDeletingKey(key.id)}
                        className="text-red-400 hover:text-red-600 p-1"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={(open) => {
        if (!open) { setShowCreateDialog(false); setCreatedKey(null); }
      }}>
        <DialogContent>
          {createdKey ? (
            <>
              <DialogHeader>
                <DialogTitle>API Key Created</DialogTitle>
                <DialogDescription>
                  Copy this key now. You won&apos;t be able to see it again.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-md">
                  <code className="text-sm font-mono break-all">{createdKey}</code>
                  <button
                    onClick={() => copyToClipboard(createdKey)}
                    className="text-amber-600 hover:text-amber-800 shrink-0"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                </div>
                <p className="text-xs text-neutral-500">
                  Store this key securely. It provides access to your organization&apos;s data.
                </p>
              </div>
              <DialogFooter>
                <Button onClick={() => { setShowCreateDialog(false); setCreatedKey(null); }}>
                  Done
                </Button>
              </DialogFooter>
            </>
          ) : (
            <>
              <DialogHeader>
                <DialogTitle>Create API Key</DialogTitle>
                <DialogDescription>
                  Create a new API key for programmatic access.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Name</label>
                  <Input
                    placeholder="e.g., Production, CI/CD, CLI"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Expiry (optional)</label>
                  <select
                    className="flex h-9 w-full rounded-md border border-neutral-200 bg-transparent px-3 py-1 text-sm"
                    value={newKeyExpiry}
                    onChange={(e) => setNewKeyExpiry(e.target.value)}
                  >
                    <option value="">No expiry</option>
                    <option value="30">30 days</option>
                    <option value="90">90 days</option>
                    <option value="180">180 days</option>
                    <option value="365">1 year</option>
                  </select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={!newKeyName || isCreating}>
                  {isCreating ? "Creating..." : "Create Key"}
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={!!deletingKey} onOpenChange={(open) => !open && setDeletingKey(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete API Key</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this API key? Any services using it will lose access.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeletingKey(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deletingKey && handleDelete(deletingKey)}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
