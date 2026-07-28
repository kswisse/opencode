"use client";

import { useState, memo, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getStatusColor, formatRelativeTime } from "@/lib/utils";
import { ArrowUp, MessageSquare, Search, Lightbulb } from "lucide-react";
import { toast } from "@/components/ui/use-toast";

interface FeedbackItem {
  id: string;
  title: string;
  description: string | null;
  status: string;
  createdAt: string;
  projectName: string;
  voteCount: number;
  commentCount: number;
}

interface Props {
  orgSlug: string;
  orgName: string;
  projects: { id: string; name: string }[];
  feedback: FeedbackItem[];
}

const FeedbackCard = memo(function FeedbackCard({
  fb,
  onVote,
}: {
  fb: FeedbackItem;
  onVote: (id: string) => void;
}) {
  return (
    <div className="flex items-start gap-4 rounded-lg border p-4">
      <button
        onClick={() => onVote(fb.id)}
        className="flex flex-col items-center gap-1 pt-1 hover:text-indigo-500 transition-colors"
        aria-label={`Vote for "${fb.title}" - ${fb.voteCount} votes`}
      >
        <ArrowUp className="h-4 w-4" aria-hidden="true" />
        <span className="text-sm font-medium">{fb.voteCount}</span>
      </button>
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="font-medium">{fb.title}</h3>
          <Badge className={getStatusColor(fb.status)} variant="secondary">
            {fb.status.replace("_", " ")}
          </Badge>
        </div>
        {fb.description && (
          <p className="mt-1 text-sm text-neutral-500">{fb.description}</p>
        )}
        <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-neutral-400">
          <span>{fb.projectName}</span>
          <span>{formatRelativeTime(fb.createdAt)}</span>
          <span className="flex items-center gap-1">
            <MessageSquare className="h-3 w-3" aria-hidden="true" /> {fb.commentCount}
          </span>
        </div>
      </div>
    </div>
  );
});

export function PublicFeedbackBoard({ orgSlug, orgName, projects, feedback: initialFeedback }: Props) {
  const [feedback, setFeedback] = useState(initialFeedback);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [projectFilter, setProjectFilter] = useState("ALL");
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [selectedProject, setSelectedProject] = useState(projects[0]?.id || "");
  const [submitting, setSubmitting] = useState(false);

  const filtered = feedback.filter((fb) => {
    if (statusFilter !== "ALL" && fb.status !== statusFilter) return false;
    if (projectFilter !== "ALL") {
      const project = projects.find((p) => p.id === projectFilter);
      if (fb.projectName !== project?.name) return false;
    }
    if (search && !fb.title.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const handleVote = useCallback(async (feedbackId: string) => {
    const res = await fetch(`/api/feedback/${feedbackId}/votes`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      setFeedback((prev) =>
        prev.map((fb) =>
          fb.id === feedbackId ? { ...fb, voteCount: data.voteCount } : fb
        )
      );
    } else {
      toast({ title: "Failed to vote", variant: "destructive" });
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !selectedProject) return;
    setSubmitting(true);

    const res = await fetch(`/api/widget/${orgSlug}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        description: description || undefined,
        email: email || undefined,
        name: name || undefined,
        projectId: selectedProject,
      }),
    });

    if (res.ok) {
      const newFb = await res.json();
      setFeedback((prev) => [
        {
          id: newFb.id,
          title: newFb.title,
          description: newFb.description,
          status: "OPEN",
          createdAt: new Date().toISOString(),
          projectName: projects.find((p) => p.id === selectedProject)?.name || "",
          voteCount: 0,
          commentCount: 0,
        },
        ...prev,
      ]);
      setTitle("");
      setDescription("");
      setEmail("");
      setName("");
      setShowForm(false);
      toast({ title: "Feedback submitted! Thank you." });
    } else {
      const err = await res.json();
      toast({ title: err.error || "Failed to submit feedback", variant: "destructive" });
    }
    setSubmitting(false);
  };

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold">{orgName} Feedback</h1>
        <p className="mt-2 text-neutral-500">
          Share your thoughts and help us improve {orgName}
        </p>
        <Button onClick={() => setShowForm(!showForm)} className="mt-4" aria-expanded={showForm}>
          <Lightbulb className="mr-2 h-4 w-4" aria-hidden="true" />
          {showForm ? "Close" : "Submit Feedback"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Submit Feedback</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4" aria-label="Submit feedback form">
              <Select value={selectedProject} onValueChange={setSelectedProject}>
                <SelectTrigger aria-label="Select project"><SelectValue placeholder="Select project" /></SelectTrigger>
                <SelectContent>
                  {projects.map((p) => (
                    <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="space-y-2">
                <label htmlFor="fb-title" className="text-sm font-medium">Title</label>
                <Input
                  id="fb-title"
                  placeholder="Summary of your feedback"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  aria-required="true"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="fb-description" className="text-sm font-medium">Description</label>
                <Textarea
                  id="fb-description"
                  placeholder="Tell us more (optional)"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label htmlFor="fb-email" className="text-sm font-medium">Email</label>
                  <Input
                    id="fb-email"
                    type="email"
                    placeholder="Your email (optional)"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="fb-name" className="text-sm font-medium">Name</label>
                  <Input
                    id="fb-name"
                    placeholder="Your name (optional)"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
              </div>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Submitting..." : "Submit Feedback"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" aria-hidden="true" />
          <Input
            placeholder="Search feedback..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
            aria-label="Search feedback"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-36" aria-label="Filter by status"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All</SelectItem>
            <SelectItem value="OPEN">Open</SelectItem>
            <SelectItem value="PLANNED">Planned</SelectItem>
            <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
            <SelectItem value="COMPLETED">Completed</SelectItem>
          </SelectContent>
        </Select>
        <Select value={projectFilter} onValueChange={setProjectFilter}>
          <SelectTrigger className="w-40" aria-label="Filter by project"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Projects</SelectItem>
            {projects.map((p) => (
              <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-3" role="list" aria-label="Feedback items">
        {filtered.map((fb) => (
          <div key={fb.id} role="listitem">
            <FeedbackCard fb={fb} onVote={handleVote} />
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="py-8 text-center text-sm text-neutral-500" role="status">
            No feedback yet. Be the first!
          </p>
        )}
      </div>
    </div>
  );
}
