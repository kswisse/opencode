import { NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { prisma } from "@/lib/prisma";
import { requireUser, apiHandler } from "@/lib/api-utils";

const VALID_PLANS = ["PRO", "BUSINESS"] as const;

export async function POST(request: Request) {
  return apiHandler(async () => {
    const auth = await requireUser(true);
    if (auth.error) return auth.error;

    const formData = await request.formData();
    const plan = formData.get("plan") as string;

    // Validate plan value
    if (!plan || !VALID_PLANS.includes(plan as typeof VALID_PLANS[number])) {
      return NextResponse.json({ error: "Invalid plan. Must be PRO or BUSINESS." }, { status: 400 });
    }

    const priceIds: Record<string, string> = {
      PRO: process.env.STRIPE_PRO_PRICE_ID!,
      BUSINESS: process.env.STRIPE_BUSINESS_PRICE_ID!,
    };

    const priceId = priceIds[plan];
    if (!priceId) {
      return NextResponse.json({ error: "Plan configuration error" }, { status: 500 });
    }

    const org = auth.user.organization;
    let customerId = org?.subscription?.stripeCustomerId;

    if (!customerId) {
      const customer = await stripe.customers.create({
        email: auth.user.email,
        name: org?.name,
        metadata: { orgId: org?.id },
      });
      customerId = customer.id;

      if (org?.id) {
        await prisma.subscription.update({
          where: { organizationId: org.id },
          data: { stripeCustomerId: customer.id },
        });
      }
    }

    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      mode: "subscription",
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard/billing?success=true`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard/billing?canceled=true`,
      metadata: { orgId: org?.id },
    });

    return NextResponse.redirect(session.url!, { status: 303 });
  }, "POST /api/checkout");
}
