import crypto from "crypto";
import { prisma } from "./prisma";

type WebhookEvent = "FEEDBACK_CREATED" | "FEEDBACK_STATUS_CHANGED" | "FEEDBACK_VOTE";

function signPayload(payload: string, secret: string): string {
  return crypto.createHmac("sha256", secret).update(payload).digest("hex");
}

async function deliverWebhook(
  webhook: { id: string; url: string; secret: string },
  event: WebhookEvent,
  payload: Record<string, unknown>
) {
  const startTime = Date.now();
  const body = JSON.stringify({ event, data: payload, timestamp: new Date().toISOString() });
  const signature = signPayload(body, webhook.secret);

  try {
    const response = await fetch(webhook.url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": event,
        "User-Agent": "SimpleFeedback-Webhook/1.0",
      },
      body,
    });

    const duration = Date.now() - startTime;
    const responseBody = await response.text();

    await prisma.webhookDelivery.create({
      data: {
        webhookId: webhook.id,
        event,
        status: response.ok ? "delivered" : "failed",
        statusCode: response.status,
        requestBody: body,
        responseBody: responseBody.substring(0, 1000),
        duration,
        retryCount: 0,
        deliveredAt: response.ok ? new Date() : null,
      },
    });

    return { success: response.ok, statusCode: response.status };
  } catch (error) {
    const duration = Date.now() - startTime;
    const errorMessage = error instanceof Error ? error.message : "Unknown error";

    await prisma.webhookDelivery.create({
      data: {
        webhookId: webhook.id,
        event,
        status: "failed",
        requestBody: body,
        responseBody: errorMessage,
        duration,
        retryCount: 0,
      },
    });

    return { success: false, statusCode: 0, error: errorMessage };
  }
}

export async function sendWebhookEvent(
  organizationId: string,
  event: WebhookEvent,
  payload: Record<string, unknown>
) {
  const webhooks = await prisma.webhook.findMany({
    where: {
      organizationId,
      active: true,
      events: { has: event },
    },
  });

  const results = await Promise.allSettled(
    webhooks.map((wh) => deliverWebhook(wh, event, payload))
  );

  return results.map((r, i) => ({
    webhookId: webhooks[i].id,
    webhookName: webhooks[i].name,
    status: r.status === "fulfilled" ? r.value : { success: false, error: "Failed to deliver" },
  }));
}

export async function getWebhookDeliveries(webhookId: string, limit = 20) {
  return prisma.webhookDelivery.findMany({
    where: { webhookId },
    orderBy: { createdAt: "desc" },
    take: limit,
  });
}

export function generateWebhookSecret(): string {
  return crypto.randomBytes(32).toString("hex");
}
