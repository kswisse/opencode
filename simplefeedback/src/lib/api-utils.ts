import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";
import { logger } from "@/lib/logger";
import type { ZodError } from "zod";
import crypto from "crypto";

// Generate a short request ID for correlating logs
export function generateRequestId(): string {
  return crypto.randomBytes(8).toString("hex");
}

// Standardized error response
export function apiError(status: number, message: string, details?: unknown) {
  return NextResponse.json(
    { error: message, ...(details ? { details } : {}) },
    { status }
  );
}

// Standardized success response
export function apiSuccess<T>(data: T, status = 200) {
  return NextResponse.json(data, { status });
}

export type AuthUserSimple = {
  id: string;
  email: string;
  name: string | null;
  avatarUrl: string | null;
  role: string;
  onboardingCompleted: boolean;
  organizationId: string;
  createdAt: Date;
  updatedAt: Date;
};

export type AuthUserWithOrg = AuthUserSimple & {
  organization: {
    id: string;
    name: string;
    slug: string;
    customDomain: string | null;
    domainVerified: boolean;
    stripeCustomerId: string | null;
    createdAt: Date;
    updatedAt: Date;
    subscription: {
      id: string;
      organizationId: string;
      stripeCustomerId: string | null;
      stripeSubscriptionId: string | null;
      plan: string;
      status: string | null;
      currentPeriodEnd: Date | null;
      createdAt: Date;
      updatedAt: Date;
    } | null;
    _count?: {
      projects: number;
      feedback: number;
    };
  };
};

// Get authenticated user from Supabase + DB
export async function getAuthUser(includeOrg?: false): Promise<AuthUserSimple | null>;
export async function getAuthUser(includeOrg: true): Promise<AuthUserWithOrg | null>;
export async function getAuthUser(includeOrg = false): Promise<unknown> {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user?.email) return null;

  const dbUser = await prisma.user.findUnique({
    where: { email: user.email },
    ...(includeOrg ? { include: { organization: { include: { subscription: true } } } } : {}),
  });
  return dbUser;
}

// Require authenticated user
export async function requireUser(includeOrg?: false): Promise<{ error: null; user: AuthUserSimple } | { error: NextResponse; user: null }>;
export async function requireUser(includeOrg: true): Promise<{ error: null; user: AuthUserWithOrg } | { error: NextResponse; user: null }>;
export async function requireUser(includeOrg: boolean = false): Promise<{ error: NextResponse | null; user: unknown }> {
  const dbUser = includeOrg ? await getAuthUser(true) : await getAuthUser(false);
  if (!dbUser) return { error: apiError(401, "Unauthorized"), user: null };
  return { error: null, user: dbUser };
}

// Require admin role
export async function requireAdmin(): Promise<{ error: null; user: AuthUserSimple } | { error: NextResponse; user: null }> {
  const result = await requireUser(false);
  if (result.error) return { error: result.error, user: null };
  if (result.user.role !== "ADMIN") return { error: apiError(403, "Forbidden"), user: null };
  return { error: null, user: result.user };
}

// Parse and validate request body with Zod schema
export async function parseBody<T>(
  request: Request,
  schema: { safeParse: (data: unknown) => { success: boolean; data?: T; error?: ZodError<unknown> } }
): Promise<{ data: T; error: null } | { data: null; error: NextResponse }> {
  try {
    const body = await request.json();
    const result = schema.safeParse(body);
    if (!result.success) {
      const zodErr = result.error as unknown as { issues?: Array<{ path: (string | number)[]; message: string }> };
      const details = zodErr.issues
        ? zodErr.issues.map((e) => ({ path: e.path.join("."), message: e.message }))
        : result.error;
      return { data: null, error: apiError(400, "Validation error", details) };
    }
    return { data: result.data as T, error: null };
  } catch {
    return { data: null, error: apiError(400, "Invalid JSON body") };
  }
}

// Parse and validate Zod schema directly (non-JSON, for query params, etc.)
export function validateSchema<T>(
  schema: { safeParse: (data: unknown) => { success: boolean; data?: T; error?: ZodError<unknown> } },
  data: unknown
): { data: T; error: null } | { data: null; error: NextResponse } {
  const result = schema.safeParse(data);
  if (!result.success) {
    const zodErr = result.error as unknown as { issues?: Array<{ path: (string | number)[]; message: string }> };
    const details = zodErr.issues
      ? zodErr.issues.map((e) => ({ path: e.path.join("."), message: e.message }))
      : result.error;
    return { data: null, error: apiError(400, "Validation error", details) };
  }
  return { data: result.data as T, error: null };
}

// Wrap API handler with error logging and request ID
export async function apiHandler<T>(
  handler: () => Promise<NextResponse>,
  context: string
): Promise<NextResponse> {
  const requestId = generateRequestId();
  try {
    return await handler();
  } catch (error) {
    logger.error(`API error in ${context} [reqId=${requestId}]`, error instanceof Error ? error : new Error(String(error)));
    return NextResponse.json(
      { error: "Internal server error", requestId },
      { status: 500 }
    );
  }
}

// Pagination helper
export function getPaginationParams(searchParams: URLSearchParams) {
  const page = Math.max(1, parseInt(searchParams.get("page") || "1", 10) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(searchParams.get("limit") || "20", 10) || 20));
  const skip = (page - 1) * limit;
  return { page, limit, skip };
}
