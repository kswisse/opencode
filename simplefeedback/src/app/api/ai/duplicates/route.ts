import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireUser, parseBody, apiHandler } from "@/lib/api-utils";
import { aiDuplicatesSchema } from "@/lib/schemas";
import { detectDuplicates } from "@/lib/ai";

export async function POST(request: Request) {
  return apiHandler(async () => {
    const auth = await requireUser(true);
    if (auth.error) return auth.error;

    const plan = auth.user.organization?.subscription?.plan;
    if (plan !== "PRO" && plan !== "BUSINESS") {
      return NextResponse.json({ error: "AI features require Pro plan" }, { status: 403 });
    }

    const parsed = await parseBody(request, aiDuplicatesSchema);
    if (parsed.error) return parsed.error;

    const { title, description } = parsed.data;

    const existing = await prisma.feedback.findMany({
      where: { organizationId: auth.user.organizationId },
      select: { id: true, title: true, description: true },
      take: 100,
    });

    const result = await detectDuplicates(title, description ?? null, existing);

    return NextResponse.json(result);
  }, "POST /api/ai/duplicates");
}
