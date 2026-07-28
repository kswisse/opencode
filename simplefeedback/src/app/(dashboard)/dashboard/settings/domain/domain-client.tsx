"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "@/components/ui/use-toast";
import { Globe, CheckCircle2, AlertCircle, RefreshCw, Trash2, ArrowRight, Copy } from "lucide-react";

interface DomainClientProps {
  currentDomain: string | null;
  isVerified: boolean;
  orgSlug: string;
  hasAccess: boolean;
  isAdmin: boolean;
}

export function DomainClient({
  currentDomain,
  isVerified,
  orgSlug,
  hasAccess,
  isAdmin,
}: DomainClientProps) {
  const router = useRouter();
  const [domain, setDomain] = useState(currentDomain || "");
  const [isSaving, setIsSaving] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [showSetupGuide, setShowSetupGuide] = useState(false);

  const verificationTxtValue = `sf-domain-verification=${orgSlug}`;

  const handleSave = async () => {
    if (!domain) return;
    setIsSaving(true);

    try {
      const res = await fetch("/api/organization/domain", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to save domain");
      }

      toast({ title: "Domain saved", description: "Add the TXT record to verify ownership." });
      setShowSetupGuide(true);
      router.refresh();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to save domain",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleVerify = async () => {
    setIsVerifying(true);

    try {
      const res = await fetch("/api/organization/domain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      const data = await res.json();

      if (data.verified) {
        toast({ title: "Domain verified!", description: data.message, variant: "success" });
        setShowSetupGuide(false);
      } else {
        toast({
          title: "Verification failed",
          description: data.message,
          variant: "destructive",
        });
      }
      router.refresh();
    } catch {
      toast({
        title: "Error",
        description: "Could not verify domain. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleRemove = async () => {
    try {
      const res = await fetch("/api/organization/domain", { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to remove domain");
      toast({ title: "Domain removed" });
      setDomain("");
      setShowRemoveDialog(false);
      router.refresh();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove domain",
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
        <Globe className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Upgrade to Business</h3>
        <p className="text-sm text-neutral-500 mb-4">
          Custom domains are available on the Business plan.
        </p>
        <a href="/dashboard/billing">
          <Button>Upgrade Now</Button>
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current Domain */}
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium">Your Domain</label>
          <div className="flex items-center gap-2 mt-1">
            <Input
              placeholder="feedback.yourcompany.com"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              disabled={!!currentDomain && isVerified}
            />
            {currentDomain && isVerified ? (
              <Badge variant="default" className="shrink-0">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Verified
              </Badge>
            ) : currentDomain ? (
              <Badge variant="secondary" className="shrink-0">
                <AlertCircle className="h-3 w-3 mr-1" />
                Unverified
              </Badge>
            ) : null}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!currentDomain ? (
            <Button onClick={handleSave} disabled={!domain || isSaving}>
              {isSaving ? "Saving..." : "Save Domain"}
            </Button>
          ) : !isVerified ? (
            <>
              <Button onClick={handleVerify} disabled={isVerifying}>
                <RefreshCw className={`h-4 w-4 mr-1 ${isVerifying ? "animate-spin" : ""}`} />
                {isVerifying ? "Verifying..." : "Verify Now"}
              </Button>
              <Button variant="outline" onClick={() => setShowSetupGuide(true)}>
                Setup Guide
              </Button>
              <Button
                variant="ghost"
                className="text-red-500"
                onClick={() => setShowRemoveDialog(true)}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Remove
              </Button>
            </>
          ) : (
            <Button
              variant="ghost"
              className="text-red-500"
              onClick={() => setShowRemoveDialog(true)}
            >
              <Trash2 className="h-4 w-4 mr-1" />
              Remove Domain
            </Button>
          )}
        </div>
      </div>

      {/* DNS Setup Guide */}
      <Dialog open={showSetupGuide} onOpenChange={setShowSetupGuide}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>DNS Setup Guide</DialogTitle>
            <DialogDescription>
              Add the following DNS records to verify and route your domain.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6">
            {/* TXT Record */}
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">1. Add TXT Record (Verification)</h4>
              <div className="bg-neutral-50 dark:bg-neutral-800/50 rounded-lg p-4 space-y-2 text-sm font-mono">
                <div className="flex justify-between">
                  <span className="text-neutral-500">Type:</span>
                  <span>TXT</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-500">Name/Host:</span>
                  <span>@ or {currentDomain}</span>
                </div>
                <div className="flex justify-between items-start gap-2">
                  <span className="text-neutral-500 shrink-0">Value:</span>
                  <div className="flex items-center gap-1">
                    <code className="text-xs break-all">{verificationTxtValue}</code>
                    <button
                      onClick={() => copyToClipboard(verificationTxtValue)}
                      className="text-neutral-400 hover:text-neutral-600 shrink-0"
                    >
                      <Copy className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* CNAME Record */}
            {currentDomain && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">2. Add CNAME Record (Routing)</h4>
                <div className="bg-neutral-50 dark:bg-neutral-800/50 rounded-lg p-4 space-y-2 text-sm font-mono">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Type:</span>
                    <span>CNAME</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Name/Host:</span>
                    <span>{currentDomain}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">Target:</span>
                    <span>simplefeedback.com</span>
                  </div>
                </div>
              </div>
            )}

            {/* SSL Note */}
            <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
              <p className="text-xs text-amber-700 dark:text-amber-300">
                <strong>Note:</strong> SSL certificates are automatically provisioned via Let&apos;s Encrypt after the domain is verified. This may take up to 15 minutes.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowSetupGuide(false)}>
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Remove Confirmation */}
      <Dialog open={showRemoveDialog} onOpenChange={setShowRemoveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove Domain</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove the custom domain? Your feedback board will revert to the default URL.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRemoveDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleRemove}>
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
