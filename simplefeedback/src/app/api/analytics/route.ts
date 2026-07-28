import { NextResponse } from "next/server";
import { trackServerEvent, identifyUser } from "@/lib/analytics";
import { createClient } from "@/lib/supabase-server";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { action, event, properties, traits } = body;

    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    const distinctId = user?.email || "anonymous";

    switch (action) {
      case "track":
        await trackServerEvent(event || "custom_event", distinctId, properties);
        break;
      case "identify":
        await identifyUser(distinctId, traits);
        break;
      default:
        return NextResponse.json({ error: "Invalid action" }, { status: 400 });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Analytics API error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
