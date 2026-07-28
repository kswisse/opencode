import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { createClient } from "@/lib/supabase-server";
import { slugify } from "@/lib/utils";
import { parseBody, apiHandler } from "@/lib/api-utils";
import { setupOrganizationSchema } from "@/lib/schemas";

export async function POST(request: Request) {
  return apiHandler(async () => {
    // Verify the caller is authenticated with Supabase
    const supabase = await createClient();
    const { data: { user: authUser }, error: authError } = await supabase.auth.getUser();
    if (authError || !authUser || !authUser.email) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const parsed = await parseBody(request, setupOrganizationSchema);
    if (parsed.error) return parsed.error;

    const { email, name, orgName } = parsed.data;

    // Ensure the email in the request matches the authenticated user's email
    if (email !== authUser.email) {
      return NextResponse.json({ error: "Email does not match authenticated user" }, { status: 403 });
    }

    // Check if user already has an organization
    const existingUser = await prisma.user.findUnique({ where: { email } });
    if (existingUser) {
      return NextResponse.json({ error: "User already has an organization" }, { status: 409 });
    }

    // Always add random suffix to avoid slug collisions
    const orgSlug = slugify(orgName) + "-" + Math.random().toString(36).slice(2, 6);

    const organization = await prisma.organization.create({
      data: {
        name: orgName,
        slug: orgSlug,
        subscription: {
          create: {
            plan: "FREE",
          },
        },
        users: {
          create: {
            email,
            name: name || null,
            role: "ADMIN",
          },
        },
      },
    });

    await prisma.project.create({
      data: {
        name: "General",
        description: "General feedback project",
        slug: "general",
        organizationId: organization.id,
      },
    });

    return NextResponse.json({ organizationId: organization.id }, { status: 201 });
  }, "POST /api/auth/setup-organization");
}
