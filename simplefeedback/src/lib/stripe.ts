import Stripe from "stripe";

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2026-06-24.dahlia",
  typescript: true,
});

export const PLANS = {
  FREE: {
    name: "Free",
    price: 0,
    seats: 1,
    projects: 1,
    feedbackLimit: 100,
    aiFeatures: false,
  },
  PRO: {
    name: "Pro",
    price: 29,
    seats: 5,
    projects: 10,
    feedbackLimit: 5000,
    aiFeatures: true,
    stripePriceId: process.env.STRIPE_PRO_PRICE_ID,
  },
  BUSINESS: {
    name: "Business",
    price: 99,
    seats: 50,
    projects: 50,
    feedbackLimit: 50000,
    aiFeatures: true,
    stripePriceId: process.env.STRIPE_BUSINESS_PRICE_ID,
  },
} as const;

export type PlanType = keyof typeof PLANS;
