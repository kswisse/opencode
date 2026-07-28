import crypto from "crypto";
import { NextResponse } from "next/server";
import { logger } from "@/lib/logger";

function verifyGithubSignature(payload: string, signature: string, secret: string): boolean {
  const computed = "sha256=" + crypto.createHmac("sha256", secret).update(payload).digest("hex");
  // Use timing-safe comparison to prevent timing attacks
  try {
    return crypto.timingSafeEqual(Buffer.from(computed), Buffer.from(signature));
  } catch {
    return false;
  }
}

export async function POST(request: Request) {
  try {
    const payload = await request.text();
    const signature = request.headers.get("x-hub-signature-256") || "";
    const event = request.headers.get("x-github-event");
    const deliveryId = request.headers.get("x-github-delivery") || "";
    const webhookSecret = process.env.GITHUB_WEBHOOK_SECRET;

    // Verify webhook signature if a secret is configured
    if (webhookSecret) {
      if (!signature) {
        logger.error("GitHub webhook: missing signature header");
        return NextResponse.json({ error: "Missing signature" }, { status: 401 });
      }

      if (!verifyGithubSignature(payload, signature, webhookSecret)) {
        logger.error("GitHub webhook: invalid signature", undefined, { deliveryId });
        return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
      }
    } else {
      logger.warn("GitHub webhook: GITHUB_WEBHOOK_SECRET not configured, skipping signature verification");
    }

    let body;
    try {
      body = JSON.parse(payload);
    } catch {
      return NextResponse.json({ error: "Invalid JSON payload" }, { status: 400 });
    }

    logger.info(`GitHub webhook received: ${event}`, { event, deliveryId, action: body.action });

    return NextResponse.json({ received: true });
  } catch (err) {
    logger.error("GitHub webhook error", err instanceof Error ? err : new Error(String(err)));
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
