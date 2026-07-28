"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { toast } from "@/components/ui/use-toast";
import {
  Webhook,
  Plus,
  Trash2,
  Copy,
  Activity,
  CheckCircle2,
  XCircle,
  ExternalLink,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

type WebhookItem = {
  id: string;
  name: string;
  url: string;
  secret: string;
  events: string[];
  active: boolean;
  createdAt: Date;
  updatedAt: Date;
  _count: { deliveries: number };
};

type WebhookDelivery = {
  id: string;
  event: string;
  status: string;
  statusCode: number | null;
  duration: number | null;
  createdAt: Date;
};

interface WebhooksClientProps {
  webhooks: WebhookItem[];
  hasAccess: boolean;
  isAdmin: boolean;
}

const EVENT_LABELS: Record<string, string> = {
  FEEDBACK_CREATED: "Feedback Created",
  FEEDBACK_STATUS_CHANGED: "Status Changed",
  FEEDBACK_VOTE: "Feedback Voted",
};

const ALL_EVENTS = ["FEEDBACK_CREATED", "FEEDBACK_STATUS_CHANGED", "FEEDBACK_VOTE"];

export function WebhooksClient({ webhooks, hasAccess, isAdmin }: WebhooksClientProps) {
  const router = useRouter();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newName, setNewName] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [newEvents, setNewEvents] = useState<string[]>(["FEEDBACK_CREATED"]);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState<string | null>(null);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [showDeliveries, setShowDeliveries] = useState(false);
  const [loadingDeliveries, setLoadingDeliveries] = useState(false);
  const [deletingWebhook, setDeletingWebhook] = useState<string | null>(null);

  const toggleEvent = (event: string) => {
    setNewEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
    );
  };

  const handleCreate = async () => {
    if (!newName || !newUrl || newEvents.length === 0) return;
    setIsCreating(true);

    try {
      const res = await fetch("/api/webhooks-manage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName, url: newUrl, events: newEvents }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to create webhook");
      }

      toast({ title: "Webhook created" });
      setShowCreateDialog(false);
      setNewName("");
      setNewUrl("");
      setNewEvents(["FEEDBACK_CREATED"]);
      router.refresh();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create webhook",
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleToggleActive = async (id: string, currentActive: boolean) => {
    try {
      const res = await fetch("/api/webhooks-manage", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, active: !currentActive }),
      });
      if (!res.ok) throw new Error("Failed to update webhook");
      router.refresh();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update webhook",
        variant: "destructive",
      });
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`/api/webhooks-manage?id=${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete webhook");
      toast({ title: "Webhook deleted" });
      setDeletingWebhook(null);
      router.refresh();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete webhook",
        variant: "destructive",
      });
    }
  };

  const loadDeliveries = async (webhookId: string) => {
    setSelectedWebhook(webhookId);
    setLoadingDeliveries(true);
    setShowDeliveries(true);
    try {
      const res = await fetch(`/api/webhooks-manage?webhookId=${webhookId}&includeDeliveries=true`);
      if (!res.ok) throw new Error("Failed to load deliveries");
      const data = await res.json();
      setDeliveries(data.deliveries || []);
    } catch {
      toast({ title: "Error", description: "Failed to load delivery logs", variant: "destructive" });
    } finally {
      setLoadingDeliveries(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({ title: "Copied to clipboard" });
  };

  if (!hasAccess) {
    return (
      <div className="text-center py-12">
        <Webhook className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Upgrade to Pro</h3>
        <p className="text-sm text-neutral-500 mb-4">
          Webhooks are available on Pro and Business plans.
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
        <Button size="sm" onClick={() => setShowCreateDialog(true)} disabled={!isAdmin}>
          <Plus className="h-4 w-4 mr-1" />
          Add Webhook
        </Button>
      </div>

      {webhooks.length === 0 ? (
        <div className="text-center py-8 text-sm text-neutral-500">
          No webhooks configured yet.
        </div>
      ) : (
        <div className="space-y-4">
          {webhooks.map((wh) => (
            <div
              key={wh.id}
              className="border border-neutral-200 dark:border-neutral-800 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div>
                    <h4 className="font-medium text-sm">{wh.name}</h4>
                    <code className="text-xs text-neutral-500">{wh.url}</code>
                  </div>
                  <Badge variant={wh.active ? "default" : "secondary"}>
                    {wh.active ? "Active" : "Disabled"}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={wh.active}
                    onCheckedChange={() => handleToggleActive(wh.id, wh.active)}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => loadDeliveries(wh.id)}
                  >
                    <Activity className="h-4 w-4 mr-1" />
                    Logs ({wh._count.deliveries})
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-red-400"
                    onClick={() => setDeletingWebhook(wh.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="flex gap-2">
                {wh.events.map((event) => (
                  <Badge key={event} variant="secondary" className="text-xs">
                    {EVENT_LABELS[event] || event}
                  </Badge>
                ))}
              </div>
              {/* Secret (hidden by default) */}
              <div className="mt-2 flex items-center gap-2">
                <code className="text-xs text-neutral-400">
                  Secret: {wh.secret.substring(0, 8)}...
                </code>
                <button
                  onClick={() => copyToClipboard(wh.secret)}
                  className="text-neutral-400 hover:text-neutral-600"
                >
                  <Copy className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Webhook</DialogTitle>
            <DialogDescription>
              Send events to your own endpoint via HTTP POST.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Name</label>
              <Input
                placeholder="e.g., Slack Notifier"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Payload URL</label>
              <Input
                placeholder="https://example.com/webhooks/simplefeedback"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Events</label>
              <div className="space-y-2 mt-1">
                {ALL_EVENTS.map((event) => (
                  <label
                    key={event}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={newEvents.includes(event)}
                      onChange={() => toggleEvent(event)}
                      className="rounded border-neutral-300"
                    />
                    <span className="text-sm">{EVENT_LABELS[event]}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newName || !newUrl || newEvents.length === 0 || isCreating}
            >
              {isCreating ? "Creating..." : "Create Webhook"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delivery Logs Dialog */}
      <Dialog open={showDeliveries} onOpenChange={setShowDeliveries}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Delivery Logs</DialogTitle>
            <DialogDescription>
              Recent webhook delivery attempts.
            </DialogDescription>
          </DialogHeader>
          {loadingDeliveries ? (
            <div className="text-center py-8 text-sm text-neutral-500">Loading...</div>
          ) : deliveries.length === 0 ? (
            <div className="text-center py-8 text-sm text-neutral-500">
              No deliveries yet.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Event</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Status Code</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {deliveries.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="text-sm">
                      {EVENT_LABELS[d.event] || d.event}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={d.status === "delivered" ? "default" : "destructive"}
                        className="text-xs"
                      >
                        {d.status === "delivered" ? (
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                        ) : (
                          <XCircle className="h-3 w-3 mr-1" />
                        )}
                        {d.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {d.statusCode || "-"}
                    </TableCell>
                    <TableCell className="text-sm">
                      {d.duration ? `${d.duration}ms` : "-"}
                    </TableCell>
                    <TableCell className="text-xs text-neutral-500">
                      {formatRelativeTime(d.createdAt)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={!!deletingWebhook} onOpenChange={(open) => !open && setDeletingWebhook(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Webhook</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this webhook? This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeletingWebhook(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deletingWebhook && handleDelete(deletingWebhook)}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
