"use client";

import { useState, memo } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getStatusColor, formatRelativeTime } from "@/lib/utils";
import { ArrowUp, MessageSquare, Search } from "lucide-react";

interface FeedbackItem {
  id: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  aiPriorityScore: number | null;
  createdAt: Date;
  project: { name: string; id: string };
  author: { name: string | null; email: string };
  _count: { votes: number; comments: number };
}

interface Props {
  feedbackItems: FeedbackItem[];
  projects: { id: string; name: string }[];
}

const FeedbackListItem = memo(function FeedbackListItem({ fb }: { fb: FeedbackItem }) {
  return (
    <Link key={fb.id} href={`/dashboard/feedback/${fb.id}`}>
      <div className="flex items-start gap-4 rounded-lg border p-4 transition-colors hover:bg-neutral-50 dark:hover:bg-neutral-900">
        <div className="flex flex-col items-center gap-1 pt-1">
          <ArrowUp className="h-4 w-4 text-neutral-400" aria-hidden="true" />
          <span className="text-sm font-medium">{fb._count.votes}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-medium truncate">{fb.title}</h3>
            <Badge className={getStatusColor(fb.status)} variant="secondary">
              {fb.status.replace("_", " ")}
            </Badge>
            {fb.aiPriorityScore && fb.aiPriorityScore >= 70 && (
              <Badge variant="destructive">High Priority</Badge>
            )}
          </div>
          {fb.description && (
            <p className="mt-1 text-sm text-neutral-500 line-clamp-1">{fb.description}</p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-neutral-400">
            <span>{fb.project.name}</span>
            <span>{fb.author.name || fb.author.email}</span>
            <span>{formatRelativeTime(fb.createdAt)}</span>
            <span className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3" aria-hidden="true" /> {fb._count.comments}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
});

const FilterBar = memo(function FilterBar({
  search,
  onSearchChange,
  statusFilter,
  onStatusChange,
  projectFilter,
  onProjectChange,
  sortBy,
  onSortChange,
  projects,
}: {
  search: string;
  onSearchChange: (v: string) => void;
  statusFilter: string;
  onStatusChange: (v: string) => void;
  projectFilter: string;
  onProjectChange: (v: string) => void;
  sortBy: string;
  onSortChange: (v: string) => void;
  projects: { id: string; name: string }[];
}) {
  return (
    <div className="flex flex-wrap gap-3">
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" aria-hidden="true" />
        <Input
          placeholder="Search feedback..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
          aria-label="Search feedback"
        />
      </div>
      <Select value={statusFilter} onValueChange={onStatusChange}>
        <SelectTrigger className="w-36" aria-label="Filter by status"><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem value="ALL">All Status</SelectItem>
          <SelectItem value="OPEN">Open</SelectItem>
          <SelectItem value="PLANNED">Planned</SelectItem>
          <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
          <SelectItem value="COMPLETED">Completed</SelectItem>
          <SelectItem value="DECLINED">Declined</SelectItem>
        </SelectContent>
      </Select>
      <Select value={projectFilter} onValueChange={onProjectChange}>
        <SelectTrigger className="w-40" aria-label="Filter by project"><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem value="ALL">All Projects</SelectItem>
          {projects.map((p) => (
            <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={sortBy} onValueChange={(v) => onSortChange(v as "newest" | "oldest" | "votes" | "priority")}>
        <SelectTrigger className="w-36" aria-label="Sort by"><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem value="newest">Newest</SelectItem>
          <SelectItem value="oldest">Oldest</SelectItem>
          <SelectItem value="votes">Most Votes</SelectItem>
          <SelectItem value="priority">AI Priority</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
});

export function FeedbackList({ feedbackItems, projects }: Props) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [projectFilter, setProjectFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState<"newest" | "oldest" | "votes" | "priority">("newest");

  const filtered = feedbackItems
    .filter((fb) => {
      if (statusFilter !== "ALL" && fb.status !== statusFilter) return false;
      if (projectFilter !== "ALL" && fb.project.id !== projectFilter) return false;
      if (search && !fb.title.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "oldest": return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
        case "votes": return b._count.votes - a._count.votes;
        case "priority": return (b.aiPriorityScore || 0) - (a.aiPriorityScore || 0);
        default: return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      }
    });

  return (
    <div className="space-y-4">
      <FilterBar
        search={search}
        onSearchChange={setSearch}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        projectFilter={projectFilter}
        onProjectChange={setProjectFilter}
        sortBy={sortBy}
        onSortChange={(v) => setSortBy(v as typeof sortBy)}
        projects={projects}
      />
      <div className="space-y-2" role="list" aria-label="Feedback items">
        {filtered.map((fb) => (
          <div key={fb.id} role="listitem">
            <FeedbackListItem fb={fb} />
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="py-8 text-center text-sm text-neutral-500" role="status">
            No feedback found matching your filters.
          </p>
        )}
      </div>
    </div>
  );
}
