import crypto from "crypto";
import { prisma } from "@/lib/prisma";
import { createAuditLog } from "@/lib/audit";

export async function createInvite(params: {
  email: string;
  role: "ADMIN" | "MEMBER";
  organizationId: string;
  invitedById: string;
  invitedByEmail: string;
}) {
  const token = crypto.randomBytes(32).toString("hex");
  const expiresAt = new Date();
  expiresAt.setDate(expiresAt.getDate() + 7); // Expires in 7 days

  const existingUser = await prisma.user.findUnique({
    where: { email: params.email },
  });

  if (existingUser && existingUser.organizationId === params.organizationId) {
    throw new Error("User is already a member of this organization");
  }

  // Check for existing pending invite
  const existingInvite = await prisma.invite.findFirst({
    where: {
      email: params.email,
      organizationId: params.organizationId,
      status: "PENDING",
    },
  });

  if (existingInvite) {
    throw new Error("An invite has already been sent to this email");
  }

  const invite = await prisma.invite.create({
    data: {
      email: params.email,
      role: params.role,
      token,
      organizationId: params.organizationId,
      invitedById: params.invitedById,
      invitedBy: params.invitedByEmail,
      expiresAt,
    },
  });

  await createAuditLog({
    action: "user.invited",
    entityType: "invite",
    entityId: invite.id,
    organizationId: params.organizationId,
    userId: params.invitedById,
    userEmail: params.invitedByEmail,
    metadata: { invitedEmail: params.email, role: params.role },
  });

  return { ...invite, inviteUrl: `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/auth/accept-invite?token=${token}` };
}

export async function acceptInvite(token: string, userId: string, userEmail: string) {
  const invite = await prisma.invite.findUnique({
    where: { token },
    include: { organization: true },
  });

  if (!invite) {
    throw new Error("Invalid invite token");
  }

  if (invite.status !== "PENDING") {
    throw new Error("This invite has already been used or expired");
  }

  if (invite.expiresAt < new Date()) {
    await prisma.invite.update({
      where: { id: invite.id },
      data: { status: "EXPIRED" },
    });
    throw new Error("This invite has expired");
  }

  if (invite.email !== userEmail) {
    throw new Error("This invite was sent to a different email address");
  }

  // Update the user's organization
  await prisma.user.update({
    where: { id: userId },
    data: {
      organizationId: invite.organizationId,
      role: invite.role,
    },
  });

  await prisma.invite.update({
    where: { id: invite.id },
    data: { status: "ACCEPTED", acceptedAt: new Date() },
  });

  return invite.organization;
}

export async function getOrganizationMembers(organizationId: string) {
  const [users, invites] = await Promise.all([
    prisma.user.findMany({
      where: { organizationId },
      select: {
        id: true,
        email: true,
        name: true,
        avatarUrl: true,
        role: true,
        createdAt: true,
      },
      orderBy: { createdAt: "asc" },
    }),
    prisma.invite.findMany({
      where: { organizationId, status: "PENDING" },
      select: {
        id: true,
        email: true,
        role: true,
        createdAt: true,
        expiresAt: true,
      },
      orderBy: { createdAt: "desc" },
    }),
  ]);

  return { users, pendingInvites: invites };
}

export async function updateMemberRole(
  organizationId: string,
  memberId: string,
  newRole: "ADMIN" | "MEMBER",
  actorId: string,
  actorEmail: string
) {
  const member = await prisma.user.findFirst({
    where: { id: memberId, organizationId },
  });

  if (!member) {
    throw new Error("Member not found");
  }

  const updated = await prisma.user.update({
    where: { id: memberId },
    data: { role: newRole },
  });

  await createAuditLog({
    action: "user.role_changed",
    entityType: "user",
    entityId: memberId,
    organizationId,
    userId: actorId,
    userEmail: actorEmail,
    metadata: { previousRole: member.role, newRole },
  });

  return updated;
}

export async function removeMember(
  organizationId: string,
  memberId: string,
  actorId: string,
  actorEmail: string
) {
  const member = await prisma.user.findFirst({
    where: { id: memberId, organizationId },
  });

  if (!member) {
    throw new Error("Member not found");
  }

  await prisma.user.delete({ where: { id: memberId } });

  await createAuditLog({
    action: "user.removed",
    entityType: "user",
    entityId: memberId,
    organizationId,
    userId: actorId,
    userEmail: actorEmail,
    metadata: { removedEmail: member.email },
  });
}

export function generateInviteEmailHtml(params: {
  inviterName: string;
  organizationName: string;
  inviteUrl: string;
  role: string;
}): string {
  return `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; background: #f5f5f5;">
  <div style="max-width: 560px; margin: 0 auto; background: white; border-radius: 8px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="text-align: center; margin-bottom: 32px;">
      <h1 style="font-size: 24px; margin: 0; color: #111;">Join ${params.organizationName} on SimpleFeedback</h1>
    </div>
    <p style="color: #555; line-height: 1.6;">Hi there,</p>
    <p style="color: #555; line-height: 1.6;">
      <strong>${params.inviterName}</strong> has invited you to join <strong>${params.organizationName}</strong> on SimpleFeedback as a <strong>${params.role}</strong>.
    </p>
    <p style="color: #555; line-height: 1.6;">
      SimpleFeedback helps teams collect, prioritize, and act on user feedback.
    </p>
    <div style="text-align: center; margin: 32px 0;">
      <a href="${params.inviteUrl}"
         style="display: inline-block; background: #111; color: white; text-decoration: none; padding: 12px 32px; border-radius: 6px; font-size: 16px; font-weight: 500;">
        Accept Invite
      </a>
    </div>
    <p style="color: #888; font-size: 12px; line-height: 1.4;">
      This invite expires in 7 days. If you weren't expecting this invite, you can safely ignore this email.
    </p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
    <p style="color: #888; font-size: 12px; text-align: center;">
      &copy; ${new Date().getFullYear()} SimpleFeedback. All rights reserved.
    </p>
  </div>
</body>
</html>`;
}
