import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase-server";
import { acceptInvite } from "@/lib/actions/invite";

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = await request.json();
  const { token } = body;

  if (!token) {
    return NextResponse.json({ error: "Token is required" }, { status: 400 });
  }

  try {
    const organization = await acceptInvite(token, user.id, user.email!);
    return NextResponse.json({ organization });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to accept invite";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
