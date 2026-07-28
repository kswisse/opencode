import { NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { prisma } from "@/lib/prisma";
import { requireUser, apiHandler } from "@/lib/api-utils";

export async function POST() {
  return apiHandler(async () => {
    const auth = await requireUser(true);
    if (auth.error) return auth.error;

    const customerId = auth.user.organization?.subscription?.stripeCustomerId;
    if (!customerId) {
      return NextResponse.json({ error: "No subscription found" }, { status: 400 });
    }

    const session = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard/billing`,
    });

    return NextResponse.json({ url: session.url });
  }, "POST /api/manage-subscription");
}
