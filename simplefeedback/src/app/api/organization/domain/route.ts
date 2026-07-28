import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { createClient } from "@/lib/supabase-server";
import { requireFeature } from "@/lib/feature-flags";
import { createAuditLog } from "@/lib/audit";
import dns from "dns";
import { promisify } from "util";

const resolveTxt = promisify(dns.resolveTxt);

const VERIFICATION_TXT_VALUE = "sf-domain-verification=";

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: { organization: { select: { customDomain: true, domainVerified: true, slug: true } } },
  });
  if (!dbUser) return NextResponse.json({ error: "Not found" }, { status: 404 });

  return NextResponse.json({
    customDomain: dbUser.organization.customDomain,
    domainVerified: dbUser.organization.domainVerified,
    verificationTxtValue: `${VERIFICATION_TXT_VALUE}${dbUser.organization.slug}`,
  });
}

export async function PUT(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: { organization: { select: { slug: true } } },
  });
  if (!dbUser || dbUser.role !== "ADMIN") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  try {
    await requireFeature(dbUser.organizationId, "custom_domains");
  } catch {
    return NextResponse.json({
      error: "Custom domains require Business plan. Please upgrade your subscription.",
    }, { status: 402 });
  }

  const body = await request.json();
  const { domain } = body;

  if (!domain) {
    return NextResponse.json({ error: "Domain is required" }, { status: 400 });
  }

  // Validate domain format
  const domainRegex = /^([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
  if (!domainRegex.test(domain)) {
    return NextResponse.json({ error: "Invalid domain format" }, { status: 400 });
  }

  // Check if domain is already taken
  const existing = await prisma.organization.findUnique({
    where: { customDomain: domain },
  });

  if (existing && existing.id !== dbUser.organizationId) {
    return NextResponse.json({ error: "Domain is already in use by another organization" }, { status: 409 });
  }

  await prisma.organization.update({
    where: { id: dbUser.organizationId },
    data: {
      customDomain: domain,
      domainVerified: false,
    },
  });

  await createAuditLog({
    action: "domain.updated",
    entityType: "domain",
    entityId: dbUser.organizationId,
    organizationId: dbUser.organizationId,
    userId: dbUser.id,
    userEmail: dbUser.email,
    metadata: { domain },
  });

  return NextResponse.json({
    customDomain: domain,
    domainVerified: false,
    verificationTxtValue: `${VERIFICATION_TXT_VALUE}${dbUser.organization.slug}`,
    message: "Domain saved. Please add the TXT record to verify ownership.",
  });
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email! },
    include: { organization: true },
  });
  if (!dbUser || dbUser.role !== "ADMIN") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const org = dbUser.organization;
  if (!org.customDomain) {
    return NextResponse.json({ error: "No custom domain configured" }, { status: 400 });
  }

  try {
    const records = await resolveTxt(org.customDomain);
    const expected = `${VERIFICATION_TXT_VALUE}${org.slug}`;
    const verified = records.some((record) =>
      record.some((txt) => txt.includes(expected))
    );

    if (verified) {
      await prisma.organization.update({
        where: { id: org.id },
        data: { domainVerified: true },
      });

      await createAuditLog({
        action: "domain.verified",
        entityType: "domain",
        entityId: org.id,
        organizationId: org.id,
        userId: dbUser.id,
        userEmail: dbUser.email,
        metadata: { domain: org.customDomain },
      });

      return NextResponse.json({ verified: true, message: "Domain verified successfully!" });
    }

    return NextResponse.json({
      verified: false,
      message: "TXT record not found. Please add the verification record and try again.",
    });
  } catch (error) {
    return NextResponse.json({
      verified: false,
      message: "Could not verify domain. Ensure the domain exists and the TXT record is propagated.",
    });
  }
}

export async function DELETE() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser || dbUser.role !== "ADMIN") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  await prisma.organization.update({
    where: { id: dbUser.organizationId },
    data: {
      customDomain: null,
      domainVerified: false,
    },
  });

  return NextResponse.json({ success: true });
}
