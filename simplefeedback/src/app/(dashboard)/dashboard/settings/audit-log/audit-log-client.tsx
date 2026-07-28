"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Search, ShieldAlert, Download } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

type AuditLogItem = {
  id: string;
  action: string;
  entityType: string;
  entityId: string | null;
  metadata: unknown;
  userId: string | null;
  userEmail: string | null;
  ipAddress: string | null;
  createdAt: Date;
};

interface AuditLogClientProps {
  logs: AuditLogItem[];
  hasAccess: boolean;
}

function formatAction(action: string): string {
  return action
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getActionColor(action: string): "default" | "destructive" | "outline" | "secondary" {
  if (action.includes("deleted") || action.includes("removed")) return "destructive";
  if (action.includes("created") || action.includes("verified") || action.includes("completed")) return "default";
  if (action.includes("updated") || action.includes("changed")) return "secondary";
  return "outline";
}

export function AuditLogClient({ logs, hasAccess }: AuditLogClientProps) {
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("all");

  if (!hasAccess) {
    return (
      <div className="text-center py-12">
        <ShieldAlert className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Upgrade to Business</h3>
        <p className="text-sm text-neutral-500 mb-4">
          Audit logs are available on the Business plan.
        </p>
        <a href="/dashboard/billing">
          <Button>Upgrade Now</Button>
        </a>
      </div>
    );
  }

  // Get unique action types for filter
  const actionTypes = [...new Set(logs.map((l) => l.action))];

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      !search ||
      log.action.toLowerCase().includes(search.toLowerCase()) ||
      (log.userEmail || "").toLowerCase().includes(search.toLowerCase()) ||
      (log.entityType || "").toLowerCase().includes(search.toLowerCase());

    const matchesAction = actionFilter === "all" || log.action === actionFilter;

    return matchesSearch && matchesAction;
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <Input
            placeholder="Search logs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={actionFilter} onValueChange={setActionFilter}>
          <SelectTrigger className="w-44">
            <SelectValue placeholder="All Actions" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Actions</SelectItem>
            {actionTypes.map((action) => (
              <SelectItem key={action} value={action}>
                {formatAction(action)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {filteredLogs.length === 0 ? (
        <div className="text-center py-8 text-sm text-neutral-500">
          {logs.length === 0
            ? "No audit logs yet. Actions will appear here as your team uses the product."
            : "No logs match your search criteria."}
        </div>
      ) : (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Action</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Details</TableHead>
                <TableHead>Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>
                    <Badge variant={getActionColor(log.action)} className="text-xs whitespace-nowrap">
                      {formatAction(log.action)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm capitalize">
                    {log.entityType.replace(/_/g, " ")}
                  </TableCell>
                  <TableCell className="text-sm text-neutral-500">
                    {log.userEmail || "System"}
                  </TableCell>
                  <TableCell className="text-xs text-neutral-400 max-w-[200px] truncate">
                    {log.metadata
                      ? JSON.stringify(log.metadata).substring(0, 60)
                      : "-"}
                  </TableCell>
                  <TableCell className="text-xs text-neutral-500 whitespace-nowrap">
                    {formatRelativeTime(log.createdAt)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-neutral-500">
        <span>{filteredLogs.length} of {logs.length} entries</span>
      </div>
    </div>
  );
}
