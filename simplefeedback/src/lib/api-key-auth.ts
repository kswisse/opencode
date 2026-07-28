import crypto from "crypto";
import { prisma } from "./prisma";

const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute
const RATE_LIMIT_MAX = 100; // requests per window

const rateLimitMap = new Map<string, { count: number; resetAt: number }>();

function checkRateLimit(key: string): boolean {
  const now = Date.now();
  const entry = rateLimitMap.get(key);

  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(key, { count: 1, resetAt: now + RATE_LIMIT_WINDOW });
    return true;
  }

  if (entry.count >= RATE_LIMIT_MAX) {
    return false;
  }

  entry.count++;
  return true;
}

export async function authenticateApiKey(request: Request): Promise<{
  authenticated: boolean;
  organizationId?: string;
  userId?: string;
  error?: string;
  status?: number;
}> {
  const authHeader = request.headers.get("Authorization");

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return { authenticated: false, error: "Missing or invalid Authorization header", status: 401 };
  }

  const apiKey = authHeader.slice(7);

  // Check rate limit by IP + key prefix
  const ip = request.headers.get("x-forwarded-for") || "unknown";
  if (!checkRateLimit(`${ip}:${apiKey.substring(0, 8)}`)) {
    return { authenticated: false, error: "Rate limit exceeded", status: 429 };
  }

  const keyRecord = await prisma.apiKey.findUnique({
    where: { key: apiKey },
    include: { organization: true },
  });

  if (!keyRecord) {
    return { authenticated: false, error: "Invalid API key", status: 401 };
  }

  if (!keyRecord.active) {
    return { authenticated: false, error: "API key is deactivated", status: 401 };
  }

  if (keyRecord.expiresAt && keyRecord.expiresAt < new Date()) {
    return { authenticated: false, error: "API key has expired", status: 401 };
  }

  // Update last used timestamp (fire and forget)
  prisma.apiKey
    .update({
      where: { id: keyRecord.id },
      data: { lastUsedAt: new Date() },
    })
    .catch(() => {});

  return {
    authenticated: true,
    organizationId: keyRecord.organizationId,
    userId: keyRecord.userId,
  };
}

export async function createApiKeyEntry(params: {
  name: string;
  key: string;
  prefix: string;
  organizationId: string;
  userId: string;
  expiresAt?: Date;
}) {
  return prisma.apiKey.create({
    data: {
      name: params.name,
      key: params.key,
      prefix: params.prefix,
      organizationId: params.organizationId,
      userId: params.userId,
      expiresAt: params.expiresAt || null,
    },
  });
}

export function generateApiKey(): { key: string; prefix: string } {
  const raw = crypto.randomBytes(32).toString("hex");
  const prefix = "sf_" + raw.substring(0, 8);
  return { key: raw, prefix };
}
