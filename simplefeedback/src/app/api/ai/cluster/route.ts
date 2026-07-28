import { NextResponse } from "next/server";
import { requireUser, apiHandler } from "@/lib/api-utils";
import { runClustering } from "@/lib/feedback";

export async function POST() {
  return apiHandler(async () => {
    const auth = await requireUser(true);
    if (auth.error) return auth.error;

    const plan = auth.user.organization?.subscription?.plan;
    if (plan !== "PRO" && plan !== "BUSINESS") {
      return NextResponse.json({ error: "AI features require Pro plan" }, { status: 403 });
    }

    const result = await runClustering(auth.user.organizationId);

    return NextResponse.json(result);
  }, "POST /api/ai/cluster");
}
