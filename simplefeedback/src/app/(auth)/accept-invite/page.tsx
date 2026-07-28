"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import Link from "next/link";

export default function AcceptInvitePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No invite token provided.");
      return;
    }

    async function accept() {
      try {
        const res = await fetch("/api/invites/accept", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        });

        const data = await res.json();

        if (res.ok) {
          setStatus("success");
          setMessage(`You've joined ${data.organization?.name || "the organization"}!`);
        } else {
          setStatus("error");
          setMessage(data.error || "Failed to accept invite");
        }
      } catch {
        setStatus("error");
        setMessage("Something went wrong. Please try again.");
      }
    }

    accept();
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>Accept Invite</CardTitle>
          <CardDescription>
            {status === "loading" && "Processing your invitation..."}
            {status === "success" && "Welcome to your new team!"}
            {status === "error" && "Invitation error"}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          {status === "loading" && (
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-neutral-400" />
          )}
          {status === "success" && (
            <CheckCircle2 className="h-12 w-12 mx-auto text-green-500" />
          )}
          {status === "error" && (
            <XCircle className="h-12 w-12 mx-auto text-red-500" />
          )}
          <p className="text-sm text-neutral-600">{message}</p>
          {status === "success" && (
            <Link href="/dashboard">
              <Button className="w-full">Go to Dashboard</Button>
            </Link>
          )}
          {status === "error" && (
            <Link href="/login">
              <Button variant="outline" className="w-full">Go to Login</Button>
            </Link>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
