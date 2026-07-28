// Runtime environment variable validation
// Called at app startup to ensure all required vars are present

export interface EnvVar {
  name: string;
  required: boolean;
  description: string;
  // If the var has a placeholder value that must be changed
  placeholderPattern?: RegExp;
}

export const REQUIRED_ENV_VARS: EnvVar[] = [
  { name: "DATABASE_URL", required: true, description: "PostgreSQL connection string" },
  { name: "NEXT_PUBLIC_SUPABASE_URL", required: true, description: "Supabase project URL" },
  { name: "NEXT_PUBLIC_SUPABASE_ANON_KEY", required: true, description: "Supabase anonymous key" },
  { name: "SUPABASE_SERVICE_ROLE_KEY", required: true, description: "Supabase service role key" },
  { name: "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY", required: false, description: "Stripe publishable key" },
  { name: "STRIPE_SECRET_KEY", required: false, description: "Stripe secret key" },
  { name: "STRIPE_WEBHOOK_SECRET", required: false, description: "Stripe webhook signing secret" },
  { name: "STRIPE_PRO_PRICE_ID", required: false, description: "Stripe Pro plan price ID" },
  { name: "STRIPE_BUSINESS_PRICE_ID", required: false, description: "Stripe Business plan price ID" },
  { name: "RESEND_API_KEY", required: false, description: "Resend email API key" },
  { name: "OPENAI_API_KEY", required: false, description: "OpenAI API key" },
  { name: "NEXT_PUBLIC_APP_URL", required: true, description: "Application public URL" },
];

export function validateEnvVars(): { valid: boolean; missing: string[]; placeholders: string[] } {
  const missing: string[] = [];
  const placeholders: string[] = [];

  for (const envVar of REQUIRED_ENV_VARS) {
    const value = process.env[envVar.name];

    if (!value && envVar.required) {
      missing.push(`${envVar.name} (${envVar.description})`);
      continue;
    }

    if (value && envVar.placeholderPattern && envVar.placeholderPattern.test(value)) {
      placeholders.push(`${envVar.name} (${envVar.description})`);
    }
  }

  return {
    valid: missing.length === 0,
    missing,
    placeholders,
  };
}

export function logEnvValidation(): void {
  const result = validateEnvVars();

  if (result.missing.length > 0) {
    console.error("❌ Missing required environment variables:");
    result.missing.forEach((v) => console.error(`   - ${v}`));
    console.error("The application may not function correctly until these are set.");
  }

  if (result.placeholders.length > 0) {
    console.warn("⚠️  Environment variables still have placeholder values:");
    result.placeholders.forEach((v) => console.warn(`   - ${v}`));
  }

  if (result.missing.length === 0 && result.placeholders.length === 0) {
    console.log("✅ All required environment variables are set.");
  }
}

// Auto-run on import in non-test environments
if (process.env.NODE_ENV !== "test") {
  logEnvValidation();
}
