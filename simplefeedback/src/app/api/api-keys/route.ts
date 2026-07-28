import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { createClient } from "@/lib/supabase-server";
import { generateApiKey } from "@/lib/api-key-auth";
import { requireFeature } from "@/lib/feature-flags";
import { createAuditLog } from "@/lib/audit";

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser) return NextResponse.json({ error: "Not found" }, { status: 404 });

  const keys = await prisma.apiKey.findMany({
    where: { organizationId: dbUser.organizationId },
    select: {
      id: true,
      name: true,
      prefix: true,
      active: true,
      lastUsedAt: true,
      expiresAt: true,
      createdAt: true,
    },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(keys);
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser || dbUser.role !== "ADMIN") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  // Check feature flag
  try {
    await requireFeature(dbUser.organizationId, "api_access");
  } catch {
    return NextResponse.json({
      error: "API access requires at least Pro plan. Please upgrade your subscription.",
    }, { status: 402 });
  }

  const body = await request.json();
  const { name, expiresInDays } = body;

  if (!name) {
    return NextResponse.json({ error: "Name is required" }, { status: 400 });
  }

  const { key, prefix } = generateApiKey();

  const expiresAt = expiresInDays
    ? new Date(Date.now() + expiresInDays * 24 * 60 * 60 * 1000)
    : null;

  const apiKey = await prisma.apiKey.create({
    data: {
      name,
      key,
      prefix,
      organizationId: dbUser.organizationId,
      userId: dbUser.id,
      expiresAt,
    },
  });

  await createAuditLog({
    action: "api_key.created",
    entityType: "api_key",
    entityId: apiKey.id,
    organizationId: dbUser.organizationId,
    userId: dbUser.id,
    userEmail: dbUser.email,
    metadata: { name, expiresInDays: expiresInDays || null },
  });

  // Return the full key only on creation
  return NextResponse.json({
    id: apiKey.id,
    name: apiKey.name,
    prefix: apiKey.prefix,
    key: apiKey.key, // Only returned once
    expiresAt: apiKey.expiresAt,
    createdAt: apiKey.createdAt,
  }, { status: 201 });
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
  const { id, name, active } = body;

  if (!id) {
    return NextResponse.json({ error: "id is required" }, { status: 400 });
  }

  const existing = await prisma.apiKey.findFirst({
    where: { id, organizationId: dbUser.organizationId },
  });

  if (!existing) {
    return NextResponse.json({ error: "API key not found" }, { status: 404 });
  }

  const updated = await prisma.apiKey.update({
    where: { id },
    data: {
      ...(name !== undefined && { name }),
      ...(active !== undefined && { active }),
    },
    select: {
      id: true,
      name: true,
      prefix: true,
      active: true,
      lastUsedAt: true,
      expiresAt: true,
      createdAt: true,
    },
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

  const existing = await prisma.apiKey.findFirst({
    where: { id, organizationId: dbUser.organizationId },
  });

  if (!existing) {
    return NextResponse.json({ error: "API key not found" }, { status: 404 });
  }

  await prisma.apiKey.delete({ where: { id } });

  await createAuditLog({
    action: "api_key.deleted",
    entityType: "api_key",
    entityId: id,
    organizationId: dbUser.organizationId,
    userId: dbUser.id,
    userEmail: dbUser.email,
    metadata: { name: existing.name },
  });

  return NextResponse.json({ success: true });
}
