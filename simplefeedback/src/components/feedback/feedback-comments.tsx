"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { formatRelativeTime } from "@/lib/utils";
import { toast } from "@/components/ui/use-toast";

interface Comment {
  id: string;
  content: string;
  createdAt: Date;
  author: { name: string | null; email: string };
}

interface Props {
  feedbackId: string;
  comments: Comment[];
}

export function FeedbackComments({ feedbackId, comments }: Props) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    setLoading(true);

    const res = await fetch(`/api/feedback/${feedbackId}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });

    if (res.ok) {
      setContent("");
      toast({ title: "Comment added" });
      router.refresh();
    } else {
      const err = await res.json();
      toast({ title: err.error || "Failed to add comment", variant: "destructive" });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-3" aria-label="Add a comment">
        <div className="space-y-2">
          <label htmlFor="comment-content" className="text-sm font-medium sr-only">
            Comment
          </label>
          <Textarea
            id="comment-content"
            placeholder="Add a comment..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={3}
            aria-required="true"
          />
        </div>
        <Button type="submit" disabled={loading || !content.trim()}>
          {loading ? "Posting..." : "Post Comment"}
        </Button>
      </form>
      {comments.length === 0 ? (
        <p className="text-sm text-neutral-500" role="status">No comments yet.</p>
      ) : (
        <div className="space-y-4" role="list" aria-label="Comments">
          {comments.map((comment) => (
            <div key={comment.id} className="flex gap-3" role="listitem">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="text-xs">
                  {(comment.author.name || comment.author.email)[0].toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium">{comment.author.name || comment.author.email}</span>
                  <span className="text-xs text-neutral-400">{formatRelativeTime(comment.createdAt)}</span>
                </div>
                <p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300 break-words">{comment.content}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
