import { NextResponse } from "next/server";
import { requireUser, parseBody, apiHandler } from "@/lib/api-utils";
import { aiPrioritySchema } from "@/lib/schemas";
import { scorePriority } from "@/lib/ai";

export async function POST(request: Request) {
  return apiHandler(async () => {
    const auth = await requireUser(true);
    if (auth.error) return auth.error;

    const plan = auth.user.organization?.subscription?.plan;
    if (plan !== "PRO" && plan !== "BUSINESS") {
      return NextResponse.json({ error: "AI features require Pro plan" }, { status: 403 });
    }

    const parsed = await parseBody(request, aiPrioritySchema);
    if (parsed.error) return parsed.error;

    const { title, description, voteCount } = parsed.data;

    const result = await scorePriority(title, description || null, voteCount);

    return NextResponse.json(result);
  }, "POST /api/ai/priority");
}
