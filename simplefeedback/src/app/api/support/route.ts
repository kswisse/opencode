import { NextResponse } from "next/server";

interface SupportTicket {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export async function POST(request: Request) {
  try {
    const body: SupportTicket = await request.json();

    // Validate required fields
    if (!body.name || !body.email || !body.subject || !body.message) {
      return NextResponse.json(
        { error: "All fields are required" },
        { status: 400 }
      );
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(body.email)) {
      return NextResponse.json(
        { error: "Invalid email address" },
        { status: 400 }
      );
    }

    // In a real production environment, this would:
    // 1. Store the ticket in the database
    // 2. Send notification to support team
    // 3. Send confirmation email to user
    //
    // For now, we log and return success

    console.log("Support ticket received:", {
      name: body.name,
      email: body.email,
      subject: body.subject,
      messageLength: body.message.length,
    });

    return NextResponse.json({
      success: true,
      message: "Support ticket submitted successfully. We'll get back to you within 24 hours.",
      ticketId: `TKT-${Date.now()}`,
    });
  } catch (error) {
    console.error("Support API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
