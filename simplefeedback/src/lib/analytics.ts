import { createClient } from "@/lib/supabase-server";

const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://app.posthog.com";
const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY || "";

type EventProperties = Record<string, string | number | boolean | null | undefined>;

/**
 * Server-side event tracking via PostHog API.
 * Falls back silently if PostHog is not configured.
 */
export async function trackServerEvent(
  event: string,
  distinctId: string,
  properties?: EventProperties
) {
  if (!POSTHOG_KEY) return;

  try {
    await fetch(`${POSTHOG_HOST}/capture/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        api_key: POSTHOG_KEY,
        event,
        distinct_id: distinctId,
        properties: {
          ...properties,
          $lib: "simplefeedback-server",
        },
      }),
    });
  } catch {
    // Silently fail - analytics should never break the app
  }
}

/**
 * Track event for the currently authenticated user.
 */
export async function trackAuthenticatedEvent(
  event: string,
  properties?: EventProperties
) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user?.email) return;
    await trackServerEvent(event, user.email, properties);
  } catch {
    // Silently fail
  }
}

/**
 * Identify a user in PostHog.
 */
export async function identifyUser(
  distinctId: string,
  traits?: Record<string, string | number | boolean>
) {
  if (!POSTHOG_KEY) return;

  try {
    await fetch(`${POSTHOG_HOST}/identify/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        api_key: POSTHOG_KEY,
        distinct_id: distinctId,
        properties: traits,
      }),
    });
  } catch {
    // Silently fail
  }
}
