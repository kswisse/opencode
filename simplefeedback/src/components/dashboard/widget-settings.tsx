"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/components/ui/use-toast";

interface Props {
  embed: {
    projectId: string;
    buttonColor: string;
    buttonText: string;
    position: string;
    title: string;
    subtitle: string;
  } | null;
  projects: { id: string; name: string }[];
  orgSlug: string;
}

export function WidgetSettings({ embed, projects, orgSlug }: Props) {
  const [projectId, setProjectId] = useState(embed?.projectId || projects[0]?.id || "");
  const [buttonColor, setButtonColor] = useState(embed?.buttonColor || "#6366f1");
  const [buttonText, setButtonText] = useState(embed?.buttonText || "Feedback");
  const [position, setPosition] = useState(embed?.position || "right");
  const [title, setTitle] = useState(embed?.title || "Share Feedback");
  const [subtitle, setSubtitle] = useState(embed?.subtitle || "Help us improve");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSave = async () => {
    setLoading(true);
    const res = await fetch("/api/widget-settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ projectId, buttonColor, buttonText, position, title, subtitle }),
    });

    if (res.ok) {
      toast({ title: "Widget settings saved" });
      router.refresh();
    } else {
      toast({ title: "Failed to save widget settings", variant: "destructive" });
    }
    setLoading(false);
  };

  const widgetScript = `<script src="${process.env.NEXT_PUBLIC_APP_URL}/api/widget-script/${orgSlug}" data-project="${projectId}" data-color="${buttonColor}" data-text="${buttonText}" data-position="${position}" data-title="${title}" data-subtitle="${subtitle}"></script>`;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Project</Label>
          <Select value={projectId} onValueChange={setProjectId}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {projects.map((p) => (
                <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Button Color</Label>
          <div className="flex gap-2">
            <Input
              type="color"
              value={buttonColor}
              onChange={(e) => setButtonColor(e.target.value)}
              className="w-12 p-1"
            />
            <Input value={buttonColor} onChange={(e) => setButtonColor(e.target.value)} />
          </div>
        </div>
        <div className="space-y-2">
          <Label>Button Text</Label>
          <Input value={buttonText} onChange={(e) => setButtonText(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Position</Label>
          <Select value={position} onValueChange={setPosition}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="right">Right</SelectItem>
              <SelectItem value="left">Left</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Widget Title</Label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Widget Subtitle</Label>
          <Input value={subtitle} onChange={(e) => setSubtitle(e.target.value)} />
        </div>
      </div>
      <Button onClick={handleSave} disabled={loading}>
        {loading ? "Saving..." : "Save Widget Settings"}
      </Button>
      <div className="space-y-2">
        <Label>Embed Code</Label>
        <div className="rounded-md bg-neutral-100 p-3 dark:bg-neutral-800">
          <code className="break-all text-xs">{widgetScript}</code>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            navigator.clipboard.writeText(widgetScript);
            toast({ title: "Copied to clipboard" });
          }}
        >
          Copy Code
        </Button>
      </div>
    </div>
  );
}
