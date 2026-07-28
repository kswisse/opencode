import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { createClient } from "@/lib/supabase-server";
import { getAuditLogs } from "@/lib/audit";
import { requireFeature } from "@/lib/feature-flags";

export async function GET(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser) return NextResponse.json({ error: "Not found" }, { status: 404 });

  try {
    await requireFeature(dbUser.organizationId, "audit_logs");
  } catch {
    return NextResponse.json({
      error: "Audit logs require Business plan. Please upgrade your subscription.",
    }, { status: 402 });
  }

  const { searchParams } = new URL(request.url);
  const limit = parseInt(searchParams.get("limit") || "50");
  const offset = parseInt(searchParams.get("offset") || "0");
  const action = searchParams.get("action") || undefined;
  const entityType = searchParams.get("entityType") || undefined;

  const result = await getAuditLogs(dbUser.organizationId, {
    limit: Math.min(limit, 100),
    offset,
    action,
    entityType,
  });

  return NextResponse.json(result);
}
