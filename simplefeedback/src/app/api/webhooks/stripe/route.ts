import { NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { prisma } from "@/lib/prisma";
import { logger } from "@/lib/logger";

// In-memory idempotency store for Stripe webhooks
// Prevents duplicate processing of the same event
const processedEvents = new Set<string>();
const IDEMPOTENCY_TTL = 60 * 60 * 1000; // 1 hour

// Clean up old entries periodically
setInterval(() => {
  // Clear every hour - Set has no TTL, but this is fine for in-memory
  // since we process webhooks from a single instance
  if (processedEvents.size > 1000) {
    processedEvents.clear();
  }
}, IDEMPOTENCY_TTL);

export async function POST(request: Request) {
  const body = await request.text();
  const signature = request.headers.get("stripe-signature") || "";

  let event;
  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err) {
    logger.error("Stripe webhook signature verification failed", err instanceof Error ? err : new Error(String(err)));
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  // Idempotency check: skip if we've already processed this event
  if (processedEvents.has(event.id)) {
    logger.info(`Stripe webhook idempotency: skipping already processed event ${event.id}`);
    return NextResponse.json({ received: true, idempotent: true });
  }

  try {
    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as unknown as Record<string, unknown>;
        const meta = (session.metadata as unknown as Record<string, string> | undefined);
        const orgId = meta?.orgId;

        if (orgId) {
          // Use upsert to handle race conditions - subscription may or may not exist
          await prisma.subscription.upsert({
            where: { organizationId: orgId },
            create: {
              organizationId: orgId,
              stripeSubscriptionId: session.subscription as string,
              plan: "PRO",
              status: "active",
              currentPeriodEnd: new Date(
                (session.current_period_end as number) * 1000
              ),
            },
            update: {
              stripeSubscriptionId: session.subscription as string,
              plan: "PRO",
              status: "active",
              currentPeriodEnd: new Date(
                (session.current_period_end as number) * 1000
              ),
            },
          });
          logger.info(`Stripe: subscription completed for org ${orgId}`);
        }
        break;
      }
      case "customer.subscription.updated":
      case "customer.subscription.deleted": {
        const subscription = event.data.object as unknown as Record<string, unknown>;
        const subMeta = subscription.metadata as unknown as Record<string, string> | undefined;
        const orgId = subMeta?.orgId ||
          await findOrgByStripeSubscription(subscription.id as string);

        if (orgId) {
          const isActive = subscription.status === "active" || subscription.status === "trialing";
          await prisma.subscription.update({
            where: { organizationId: orgId },
            data: {
              status: subscription.status as string,
              plan: isActive ? "PRO" : "FREE",
              stripeSubscriptionId:
                isActive ? (subscription.id as string) : null,
              currentPeriodEnd: subscription.current_period_end
                ? new Date((subscription.current_period_end as number) * 1000)
                : null,
            },
          });
          logger.info(`Stripe: subscription ${event.type} for org ${orgId} (status=${subscription.status})`);
        }
        break;
      }
    }

    // Mark event as processed for idempotency
    processedEvents.add(event.id);
  } catch (err) {
    logger.error("Stripe webhook handler error", err instanceof Error ? err : new Error(String(err)));
    return NextResponse.json({ error: "Webhook handler error" }, { status: 500 });
  }

  return NextResponse.json({ received: true });
}

// Fallback: find org by stripe subscription ID
async function findOrgByStripeSubscription(subscriptionId: string): Promise<string | null> {
  const sub = await prisma.subscription.findFirst({
    where: { stripeSubscriptionId: subscriptionId },
    select: { organizationId: true },
  });
  return sub?.organizationId || null;
}
