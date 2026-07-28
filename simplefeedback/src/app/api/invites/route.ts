import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { createClient } from "@/lib/supabase-server";
import { createInvite, getOrganizationMembers, updateMemberRole, removeMember, generateInviteEmailHtml } from "@/lib/actions/invite";
import { checkSeatLimit } from "@/lib/limits";

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser) return NextResponse.json({ error: "Not found" }, { status: 404 });

  const members = await getOrganizationMembers(dbUser.organizationId);
  return NextResponse.json(members);
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const dbUser = await prisma.user.findUnique({ where: { email: user.email! } });
  if (!dbUser || dbUser.role !== "ADMIN") {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const body = await request.json();
  const { email, role } = body;

  if (!email) {
    return NextResponse.json({ error: "Email is required" }, { status: 400 });
  }

  // Check seat limit
  const seatCheck = await checkSeatLimit(dbUser.organizationId);
  if (!seatCheck.allowed) {
    return NextResponse.json({
      error: `Seat limit reached (${seatCheck.current}/${seatCheck.limit}). Please upgrade your plan to invite more members.`,
      limitCheck: seatCheck,
    }, { status: 402 });
  }

  try {
    const invite = await createInvite({
      email,
      role: role || "MEMBER",
      organizationId: dbUser.organizationId,
      invitedById: dbUser.id,
      invitedByEmail: dbUser.email,
    });

    // Generate email HTML
    const org = await prisma.organization.findUnique({ where: { id: dbUser.organizationId } });
    const emailHtml = generateInviteEmailHtml({
      inviterName: dbUser.name || dbUser.email,
      organizationName: org?.name || "Unknown Organization",
      inviteUrl: invite.inviteUrl,
      role: invite.role,
    });

    return NextResponse.json({
      ...invite,
      emailHtml, // Return HTML for preview - actual sending would use Resend
    }, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to create invite";
    return NextResponse.json({ error: message }, { status: 400 });
  }
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
  const { memberId, role } = body;

  if (!memberId || !role) {
    return NextResponse.json({ error: "memberId and role are required" }, { status: 400 });
  }

  try {
    const updated = await updateMemberRole(
      dbUser.organizationId,
      memberId,
      role,
      dbUser.id,
      dbUser.email
    );
    return NextResponse.json(updated);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to update member role";
    return NextResponse.json({ error: message }, { status: 400 });
  }
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
  const memberId = searchParams.get("memberId");

  if (!memberId) {
    return NextResponse.json({ error: "memberId is required" }, { status: 400 });
  }

  if (memberId === dbUser.id) {
    return NextResponse.json({ error: "Cannot remove yourself" }, { status: 400 });
  }

  try {
    await removeMember(
      dbUser.organizationId,
      memberId,
      dbUser.id,
      dbUser.email
    );
    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to remove member";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
