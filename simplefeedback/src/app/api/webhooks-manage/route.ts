import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { createClient } from "@/lib/supabase-server";
import { requireFeature } from "@/lib/feature-flags";
import { createAuditLog } from "@/lib/audit";
import { generateWebhookSecret, getWebhookDeliveries } from "@/lib/webhooks";

const VALID_EVENTS = ["FEEDBACK_CREATED", "FEEDBACK_STATUS_CHANGED", "FEEDBACK_VOTE"] as const;

export async function GET(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser) return NextResponse.json({ error: "Not found" }, { status: 404 });

  const { searchParams } = new URL(request.url);
  const webhookId = searchParams.get("webhookId");
  const includeDeliveries = searchParams.get("includeDeliveries") === "true";

  if (webhookId && includeDeliveries) {
    const webhook = await prisma.webhook.findFirst({
      where: { id: webhookId, organizationId: dbUser.organizationId },
    });
    if (!webhook) return NextResponse.json({ error: "Webhook not found" }, { status: 404 });

    const deliveries = await getWebhookDeliveries(webhookId);
    return NextResponse.json({ webhook, deliveries });
  }

  const webhooks = await prisma.webhook.findMany({
    where: { organizationId: dbUser.organizationId },
    include: { _count: { select: { deliveries: true } } },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(webhooks);
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser || dbUser.role !== "ADMIN") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  try {
    await requireFeature(dbUser.organizationId, "webhooks");
  } catch {
    return NextResponse.json({
      error: "Webhooks require at least Pro plan. Please upgrade your subscription.",
    }, { status: 402 });
  }

  const body = await request.json();
  const { name, url, events } = body;

  if (!name || !url || !events || !Array.isArray(events) || events.length === 0) {
    return NextResponse.json({ error: "name, url, and events are required" }, { status: 400 });
  }

  // Validate events
  for (const event of events) {
    if (!VALID_EVENTS.includes(event)) {
      return NextResponse.json({ error: `Invalid event: ${event}` }, { status: 400 });
    }
  }

  // Validate URL
  try {
    new URL(url);
  } catch {
    return NextResponse.json({ error: "Invalid URL" }, { status: 400 });
  }

  const secret = generateWebhookSecret();

  const webhook = await prisma.webhook.create({
    data: {
      name,
      url,
      secret,
      events,
      organizationId: dbUser.organizationId,
    },
  });

  await createAuditLog({
    action: "webhook.created",
    entityType: "webhook",
    entityId: webhook.id,
    organizationId: dbUser.organizationId,
    userId: dbUser.id,
    userEmail: dbUser.email,
    metadata: { name, url, events },
  });

  return NextResponse.json(webhook, { status: 201 });
}

export async function PUT(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser || dbUser.role !== "ADMIN") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const body = await request.json();
  const { id, name, url, events, active } = body;

  if (!id) {
    return NextResponse.json({ error: "id is required" }, { status: 400 });
  }

  const existing = await prisma.webhook.findFirst({
    where: { id, organizationId: dbUser.organizationId },
  });

  if (!existing) {
    return NextResponse.json({ error: "Webhook not found" }, { status: 404 });
  }

  if (events) {
    for (const event of events) {
      if (!VALID_EVENTS.includes(event)) {
        return NextResponse.json({ error: `Invalid event: ${event}` }, { status: 400 });
      }
    }
  }

  if (url) {
    try { new URL(url); } catch {
      return NextResponse.json({ error: "Invalid URL" }, { status: 400 });
    }
  }

  const updated = await prisma.webhook.update({
    where: { id },
    data: {
      ...(name !== undefined && { name }),
      ...(url !== undefined && { url }),
      ...(events !== undefined && { events }),
      ...(active !== undefined && { active }),
    },
  });

  await createAuditLog({
    action: "webhook.updated",
    entityType: "webhook",
    entityId: id,
    organizationId: dbUser.organizationId,
    userId: dbUser.id,
    userEmail: dbUser.email,
    metadata: { name, url, events, active },
  });

  return NextResponse.json(updated);
}

export async function DELETE(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser || dbUser.role !== "ADMIN") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");

  if (!id) {
    return NextResponse.json({ error: "id is required" }, { status: 400 });
  }

  const existing = await prisma.webhook.findFirst({
    where: { id, organizationId: dbUser.organizationId },
  });

  if (!existing) {
    return NextResponse.json({ error: "Webhook not found" }, { status: 404 });
  }

  await prisma.webhook.delete({ where: { id } });

  await createAuditLog({
    action: "webhook.deleted",
    entityType: "webhook",
    entityId: id,
    organizationId: dbUser.organizationId,
    userId: dbUser.id,
    userEmail: dbUser.email,
    metadata: { name: existing.name },
  });

  return NextResponse.json({ success: true });
}
