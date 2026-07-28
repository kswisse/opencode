"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";
import { useDebounce } from "@/hooks/use-debounce";
import Link from "next/link";
import { Plus, Search, Newspaper } from "lucide-react";

interface ChangelogItem {
  id: string;
  title: string;
  content: string;
  publishedAt: string | null;
  createdAt: string;
  project: { name: string } | null;
}

interface Props {
  changelogs: ChangelogItem[];
}

export function ChangelogsList({ changelogs }: Props) {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);

  const filtered = useMemo(
    () =>
      changelogs.filter((cl) => {
        if (!debouncedSearch) return true;
        const q = debouncedSearch.toLowerCase();
        return (
          cl.title.toLowerCase().includes(q) ||
          cl.content.toLowerCase().includes(q) ||
          (cl.project?.name || "").toLowerCase().includes(q)
        );
      }),
    [changelogs, debouncedSearch]
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Changelogs</h1>
          <p className="text-neutral-500">Release notes and product updates</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href="/api/ai/release-notes">Generate with AI</Link>
          </Button>
          <Button asChild>
            <Link href="/dashboard/changelogs/new">
              <Plus className="mr-2 h-4 w-4" /> New Changelog
            </Link>
          </Button>
        </div>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
        <Input
          placeholder="Search changelogs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {debouncedSearch && (
        <p className="text-sm text-neutral-500">
          {filtered.length} result{filtered.length !== 1 ? "s" : ""} for &quot;{debouncedSearch}&quot;
        </p>
      )}

      <div className="space-y-4">
        {filtered.map((cl) => (
          <Card key={cl.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{cl.title}</CardTitle>
                {cl.publishedAt ? (
                  <span className="text-xs text-neutral-500">{formatDate(cl.publishedAt)}</span>
                ) : (
                  <span className="text-xs text-yellow-500">Draft</span>
                )}
              </div>
              {cl.project && <p className="text-xs text-neutral-400">{cl.project.name}</p>}
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm dark:prose-invert max-w-none line-clamp-3">
                {cl.content}
              </div>
            </CardContent>
          </Card>
        ))}
        {filtered.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center py-12 text-center">
              <div className="rounded-full bg-neutral-100 p-3 dark:bg-neutral-800">
                <Newspaper className="h-6 w-6 text-neutral-400" />
              </div>
              <p className="mt-4 text-sm font-medium text-neutral-700 dark:text-neutral-300">
                {debouncedSearch
                  ? 'No results found for "' + debouncedSearch + '"'
                  : "No changelogs published yet."}
              </p>
              <p className="mt-1 text-xs text-neutral-500">
                {debouncedSearch
                  ? "Try a different search term"
                  : "Create one to keep users informed about updates."}
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
