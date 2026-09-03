# French Exam Trainer — Implementation Plan

**Date:** 2026-09-03
**Spec:** `docs/superpowers/specs/2026-09-03-french-exam-trainer-design.md`
**Scope:** Phase 1-3 (Exam Engine, Question Bank, Exam Import)

---

## Overview

This plan is organized into 3 phases with 22 sequential tasks. Each task is self-contained and produces a testable deliverable. Tasks within a phase can be executed sequentially by a coding agent.

**Dependency graph:**
```
T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09 → T10 → T11
                                                              ↓
T12 → T13 → T14 → T15 → T16 → T17 → T18 → T19 → T20 → T21 → T22
```

---

# PHASE 1 — Core Exam Engine (Tasks T01–T11)

---

## T01: Project Scaffolding & Dependencies

**Goal:** Create the Next.js project with all dependencies installed and configured.

**Files to create:**
```
french-exam-trainer/
├── package.json
├── tsconfig.json
├── next.config.ts
├── postcss.config.mjs
├── .env.local
├── .env.example
├── .gitignore
├── eslint.config.mjs
└── src/
    └── app/
        ├── layout.tsx
        ├── page.tsx
        └── globals.css
```

**Dependencies (package.json):**
```json
{
  "name": "french-exam-trainer",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint",
    "test": "vitest",
    "db:generate": "prisma generate",
    "db:push": "prisma db push",
    "db:migrate": "prisma migrate dev",
    "db:seed": "tsx prisma/seed/seed.ts"
  },
  "dependencies": {
    "next": "16.2.11",
    "react": "19.2.4",
    "react-dom": "19.2.4",
    "@prisma/adapter-pg": "^7.9.0",
    "@prisma/client": "^7.9.0",
    "@supabase/ssr": "^0.12.3",
    "@supabase/supabase-js": "^2.110.8",
    "zod": "^4.4.3",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.6.0",
    "lucide-react": "^1.26.0",
    "date-fns": "^4.4.0",
    "pdf-parse": "^1.1.1",
    "tesseract.js": "^5.1.1",
    "@google/generative-ai": "^0.21.0"
  },
  "devDependencies": {
    "prisma": "^7.9.0",
    "tsx": "^4.23.1",
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "@tailwindcss/postcss": "^4",
    "tailwindcss": "^4",
    "eslint": "^9",
    "eslint-config-next": "16.2.11",
    "vitest": "^4.1.10",
    "pg": "^8.22.0",
    "@types/pg": "^8.20.0"
  },
  "prisma": {
    "seed": "tsx prisma/seed/seed.ts"
  }
}
```

**Config files:**

`next.config.ts` — Follow simplefeedback pattern:
```ts
import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  serverExternalPackages: ["@prisma/client", "pdf-parse", "tesseract.js"],
};
export default nextConfig;
```

`postcss.config.mjs`:
```js
const config = { plugins: { "@tailwindcss/postcss": {} } };
export default config;
```

`tsconfig.json` — Follow simplefeedback pattern:
```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules", "prisma/seed"]
}
```

`.env.example`:
```
DATABASE_URL=postgresql://...
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
GOOGLE_AI_API_KEY=...
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**`src/app/globals.css`:**
```css
@import "tailwindcss";

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --color-destructive: var(--destructive);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-success: var(--success);
  --color-warning: var(--warning);
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
}

:root {
  --background: #ffffff;
  --foreground: #0a0a0a;
  --primary: #1e40af;
  --primary-foreground: #ffffff;
  --muted: #f5f5f5;
  --muted-foreground: #737373;
  --border: #e5e5e5;
  --input: #e5e5e5;
  --ring: #1e40af;
  --destructive: #dc2626;
  --accent: #f5f5f5;
  --accent-foreground: #0a0a0a;
  --card: #ffffff;
  --card-foreground: #0a0a0a;
  --popover: #ffffff;
  --popover-foreground: #0a0a0a;
  --success: #16a34a;
  --warning: #d97706;
}

.dark {
  --background: #0a0a0a;
  --foreground: #fafafa;
  --primary: #3b82f6;
  --primary-foreground: #0a0a0a;
  --muted: #262626;
  --muted-foreground: #a3a3a3;
  --border: #262626;
  --input: #262626;
  --ring: #3b82f6;
  --destructive: #ef4444;
  --accent: #262626;
  --accent-foreground: #fafafa;
  --card: #171717;
  --card-foreground: #fafafa;
  --popover: #171717;
  --popover-foreground: #fafafa;
  --success: #22c55e;
  --warning: #f59e0b;
}
```

**`src/app/layout.tsx`:**
```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "French Exam Trainer",
  description: "Practice French exams with AI-powered analysis",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
```

**`src/app/page.tsx`:** Simple landing page with redirect to dashboard.

**Authorization:** None needed for scaffolding.

**Tests:** None for scaffolding.

**Acceptance criteria:**
- `npm run dev` starts without errors
- `npm run build` completes without errors
- TypeScript compiles without errors
- Tailwind CSS works (verified by background color in browser)

**Dependencies:** None (first task).

---

## T02: Prisma Schema & Database Setup

**Goal:** Define the complete database schema and generate the Prisma client.

**Files to create:**
```
french-exam-trainer/
├── prisma/
│   ├── schema.prisma
│   └── config.ts
└── src/
    └── lib/
        └── db.ts          # Prisma client singleton
```

**`prisma/schema.prisma`:** Copy the complete schema from spec Section 4, including all 16 models, 10 enums, all indexes, and all cascade annotations. Key points:

```prisma
generator client {
  provider        = "prisma-client"
  output          = "../src/generated/prisma"
  previewFeatures = ["multiSchema"]
}

datasource db {
  provider  = "postgresql"
  url       = env("DATABASE_URL")
  directUrl = env("DIRECT_URL")
}

// All 16 models from spec Section 4.1-4.3
// All 10 enums from spec Section 4.4
// All @@index directives
// All cascade comments as documentation
```

**Important cascade rules to implement in Prisma:**
- Profile → ExamAttempt: `onDelete: Cascade`
- Profile → Mistake: `onDelete: Cascade`
- Exam → ExamSection: `onDelete: Cascade`
- Exam → ExamAttempt: `onDelete: Cascade`
- Exam → ExamSource: `onDelete: Cascade`
- Exam → ContentImport: `onDelete: Cascade`
- ExamSection → Passage: `onDelete: Cascade`
- ExamSection → Question: `onDelete: Cascade`
- Passage → Question: `onDelete: Restrict`
- Question → QuestionOption: `onDelete: Cascade`
- Question → QuestionAnswer: `onDelete: Cascade`
- Question → QuestionSkill: `onDelete: Cascade`
- Question → QuestionVersion: `onDelete: Cascade`
- Question → QuestionAttempt: `onDelete: Restrict`
- QuestionOption → QuestionAttempt: `onDelete: Restrict`
- ExamAttempt → QuestionAttempt: `onDelete: Cascade`
- QuestionAttempt → Mistake: `onDelete: Cascade`
- Document → ContentImport: `onDelete: Cascade`
- Document → ExamSource: `onDelete: Cascade`
- Skill → children: `onDelete: SetNull`
- Skill → QuestionSkill: `onDelete: Restrict`

**`prisma/config.ts`:**
```ts
import { defineConfig } from "prisma/config";
export default defineConfig({ earlyAccess: true, schema: "prisma/schema.prisma" });
```

**`src/lib/db.ts`:** Follow simplefeedback pattern exactly:
```ts
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "@/generated/prisma/client";

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

function createPrismaClient() {
  const connectionString = process.env.DATABASE_URL!;
  const adapter = new PrismaPg({ connectionString });
  return new PrismaClient({ adapter });
}

export const prisma = globalForPrisma.prisma ?? createPrismaClient();
if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
```

**After creating schema, run:**
```bash
npx prisma generate
npx prisma db push
```

**Tests:** None (schema only).

**Acceptance criteria:**
- `npx prisma generate` succeeds
- `npx prisma db push` applies to database
- `src/generated/prisma/client` exports all models and enums
- TypeScript imports from `@/generated/prisma/client` work

**Dependencies:** T01.

---

## T03: UI Component Library (shadcn/ui)

**Goal:** Install and configure shadcn/ui components needed for V1.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── components/
│   │   └── ui/
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── input.tsx
│   │       ├── label.tsx
│   │       ├── select.tsx
│   │       ├── dialog.tsx
│   │       ├── skeleton.tsx
│   │       ├── badge.tsx
│   │       ├── tabs.tsx
│   │       ├── textarea.tsx
│   │       ├── separator.tsx
│   │       ├── toast.tsx
│   │       ├── toaster.tsx
│   │       ├── tooltip.tsx
│   │       └── progress.tsx
│   └── lib/
│       └── utils.ts        # cn() utility
```

**`src/lib/utils.ts`:**
```ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }
```

**Components:** Follow simplefeedback pattern — cva + forwardRef + Radix primitives. Install via shadcn CLI or copy from simplefeedback.

**Tests:** None.

**Acceptance criteria:**
- All components render without errors
- `cn()` utility works
- Button variants (default, destructive, outline, secondary, ghost, link) work
- Card, Input, Select, Dialog all functional

**Dependencies:** T01.

---

## T04: Authentication & Middleware

**Goal:** Implement Supabase auth with login/register, middleware protection, and Profile creation.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── lib/
│   │   ├── supabase-server.ts
│   │   ├── supabase-client.ts
│   │   ├── supabase-middleware.ts
│   │   └── auth.ts
│   ├── middleware.ts
│   └── app/
│       ├── (auth)/
│       │   ├── layout.tsx
│       │   ├── login/
│       │   │   └── page.tsx
│       │   └── register/
│       │       └── page.tsx
│       └── api/
│           └── auth/
│               └── callback/
│                   └── route.ts
```

**`src/lib/supabase-server.ts`:** Follow simplefeedback pattern:
```ts
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createClient() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll(); },
        setAll(cookiesToSet) {
          try { cookiesToSet.forEach(({ name, value, options }) => cookieStore.set(name, value, options)); }
          catch {}
        },
      },
    }
  );
}
```

**`src/lib/supabase-client.ts`:**
```ts
import { createBrowserClient } from "@supabase/ssr";
export function createClient() {
  return createServerClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);
}
```

**`src/lib/supabase-middleware.ts`:** Follow simplefeedback pattern — refresh session, protect `/dashboard`, `/admin`, `/api/attempts`, `/api/exams` routes.

**`src/lib/auth.ts`:**
```ts
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/db";

export async function getCurrentUser() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return null;
  return prisma.profile.findUnique({ where: { id: user.id } });
}

export async function requireUser() {
  const user = await getCurrentUser();
  if (!user) throw new Error("Unauthorized");
  return user;
}

export async function requireAdmin() {
  const user = await requireUser();
  if (user.role !== "ADMIN") throw new Error("Forbidden");
  return user;
}
```

**`src/middleware.ts`:**
```ts
import { updateSession } from "@/lib/supabase-middleware";
import { type NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  return await updateSession(request);
}
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
```

**Profile creation:** On first login, create Profile record. Implement in auth callback route or via database trigger.

**API auth helper (for later tasks):**
```ts
// src/lib/api-utils.ts
import { NextResponse } from "next/server";
import { getCurrentUser } from "./auth";

export async function getAuthUser() {
  const user = await getCurrentUser();
  if (!user) return { error: NextResponse.json({ error: "Unauthorized" }, { status: 401 }), user: null };
  return { error: null, user };
}

export function apiError(status: number, message: string) {
  return NextResponse.json({ error: message }, { status });
}

export function apiSuccess(data: unknown, status = 200) {
  return NextResponse.json(data, { status });
}
```

**Tests:** None (manual testing with Supabase dashboard).

**Acceptance criteria:**
- Login page renders and submits to Supabase
- Register page creates Supabase user + Profile record
- Middleware redirects unauthenticated users from `/dashboard/*` to `/login`
- `getCurrentUser()` returns Profile for authenticated users
- `requireAdmin()` throws for non-admin users

**Dependencies:** T01, T02.

---

## T05: Scoring Engine (Domain Logic)

**Goal:** Implement the deterministic scoring engine with all question types.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── services/
│   │   └── scoring.ts
│   └── types/
│       └── scoring.ts
└── tests/
    └── unit/
        └── scoring.test.ts
```

**`src/types/scoring.ts`:**
```ts
import { type QuestionType, type QuestionSnapshot } from "@/generated/prisma/client";

export interface ScoringConfig {
  points: number;
  negativePoints: number;
}

export interface GradeResult {
  isCorrect: boolean | null;  // null for WRITING
  pointsAwarded: number;
}

export interface ExamResult {
  totalScore: number;
  totalPossible: number;
  percentage: number;
  timeSpentSeconds: number;
  sectionResults: SectionResult[];
  questionResults: QuestionResult[];
  correctCount: number;
  incorrectCount: number;
  unansweredCount: number;
  accuracy: number;
}

export interface SectionResult {
  sectionId: string;
  sectionTitle: string;
  score: number;
  totalPossible: number;
  percentage: number;
}

export interface QuestionResult {
  questionId: string;
  questionNumber: number;
  isCorrect: boolean | null;
  pointsAwarded: number;
  selectedOptionId?: string;
  textAnswer?: string;
}
```

**`src/services/scoring.ts`:**
```ts
// gradeAnswer(snapshot, selectedOptionId, textAnswer, config) → GradeResult
// - MULTIPLE_CHOICE / TRUE_FALSE: compare selectedOptionId to correct option
// - SHORT_TEXT: compare textAnswer against QuestionAnswer records with normalization
// - FILL_BLANK: parse JSON array, compare each blank against QuestionAnswer
// - MATCHING: parse JSON objects, compare pairings
// - WRITING: return { isCorrect: null, pointsAwarded: 0 }

// normalizeText(text, rules?) → string
// - trimWhitespace, caseInsensitive, removeAccents

// calculateExamResult(attempt, questions, sections) → ExamResult
// - Sum pointsAwarded, compute totals, section breakdowns

// calculateTotalPossible(questions) → number
// - SUM(question.points) for all questions
```

**Implementation details:**

`gradeAnswer` function:
1. Switch on `snapshot.type`
2. For MC/TF: find option where `isCorrect === true` in snapshot, compare with `selectedOptionId`
3. For SHORT_TEXT: iterate `snapshot.answers`, normalize both texts, check match
4. For FILL_BLANK: parse `textAnswer` as JSON array, for each blank iterate answers with matching blank prefix
5. For MATCHING: parse both `textAnswer` and expected answer as JSON, compare key-value pairs
6. For WRITING: return null
7. Return `{ isCorrect, pointsAwarded }` where pointsAwarded = isCorrect ? config.points : -config.negativePoints

`normalizeText` function:
1. Apply trimWhitespace (default true)
2. Apply caseInsensitive (default true)
3. Apply removeAccents using Unicode normalization

**Tests (`tests/unit/scoring.test.ts`):**
```ts
describe("scoring engine", () => {
  describe("gradeAnswer", () => {
    test("MC correct answer → full points")
    test("MC incorrect answer → 0 points")
    test("TF correct answer → full points")
    test("SHORT_TEXT exact match → full points")
    test("SHORT_TEXT case-insensitive match → full points")
    test("SHORT_TEXT with accent normalization → full points")
    test("SHORT_TEXT no match → 0 points")
    test("FILL_BLANK all correct → full points")
    test("FILL_BLANK partial correct → 0 points")
    test("MATCHING all correct → full points")
    test("MATCHING partial → 0 points")
    test("WRITING → null isCorrect, 0 points")
    test("negative points applied on incorrect")
  });

  describe("normalizeText", () => {
    test("trims whitespace")
    test("lowercases")
    test("removes accents (é → e)")
  });

  describe("calculateExamResult", () => {
    test("computes total score correctly")
    test("computes section breakdown")
    test("computes accuracy percentage")
  });
});
```

**Acceptance criteria:**
- All 15+ test cases pass
- Scoring is pure function (no side effects, no DB calls)
- WRITING returns null isCorrect
- Normalization handles French accents

**Dependencies:** T02.

---

## T06: Seed Data

**Goal:** Create demo exam with 20 original French questions across 3 sections, plus skill taxonomy.

**Files to create:**
```
french-exam-trainer/
└── prisma/
    └── seed/
        └── seed.ts
```

**`prisma/seed/seed.ts`:**

Create a script that:
1. Upserts the skill taxonomy (8 skills from spec Section 19.2)
2. Creates a demo admin Profile
3. Creates one Exam: "Exercices de Français — Démo" with status=PUBLISHED, mode=BOTH
4. Creates 3 ExamSections with correct order
5. Creates 20 Questions across sections with correct types, points, order
6. Creates QuestionOption records for MC/TF questions
7. Creates QuestionAnswer records for SHORT_TEXT/FILL_BLANK/MATCHING
8. Creates QuestionSkill associations

**Skill taxonomy to seed:**
```ts
const skills = [
  { name: "Compréhension écrite", category: "receptive" },
  { name: "Grammaire", category: "linguistic" },
  { name: "Temps verbaux", parentId: "<grammaire-id>", category: "linguistic" },
  { name: "Subjonctif", parentId: "<grammaire-id>", category: "linguistic" },
  { name: "Conditionnel", parentId: "<grammaire-id>", category: "linguistic" },
  { name: "Pronoms", parentId: "<grammaire-id>", category: "linguistic" },
  { name: "Prépositions", parentId: "<grammaire-id>", category: "linguistic" },
  { name: "Vocabulaire", category: "linguistic" },
  { name: "Inférence", category: "cognitive" },
];
```

**Question content:** Create original French questions. Examples:

Section 1 — Compréhension écrite (5 questions):
- Q1 (MC): "Quelle est la capitale de la France?" Options: A) Lyon B) Paris C) Marseille D) Toulouse. Correct: B
- Q2 (MC): "Que signifie 'avoir le coup de foudre'?" Options with French idioms. Correct: "Tomber amoureux"
- Q3 (TF): "Le subjonctif est obligatoire après 'croire que'." Correct: False
- Q4 (SHORT_TEXT): "Conjuguez 'aller' au présent, 1ère personne du singulier." Acceptable: ["vais"]
- Q5 (MC): Reading comprehension passage + question about main idea

Section 2 — Grammaire (8 questions):
- Q6 (MC): Temps verbaux — "Quel temps est utilisé dans: 'Je mangeais un gâteau'?"
- Q7 (MC): Subjonctif — "Il faut que tu ___ (aller)"
- Q8 (FILL_BLANK): "Je ___ (être) allé au marché ___ (hier)"
- Q9 (MATCHING): Match French words to English translations
- etc.

Section 3 — Vocabulaire (7 questions):
- Q10 (MC): "Que signifie 'une arche'?" Context-based vocabulary
- etc.

**Tests:** None (seed script only).

**Acceptance criteria:**
- `npx tsx prisma/seed/seed.ts` runs without errors
- Database contains: 1 Exam, 3 Sections, 20 Questions, all Options/Answers
- All QuestionSkill associations created
- `npm run build` still works after seeding

**Dependencies:** T02.

---

## T07: Exam List & Detail Pages

**Goal:** Build the exam browsing interface — list published exams and view exam details.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── exams/
│   │       ├── services/
│   │       │   └── exam.ts         # getPublishedExams, getExamById
│   │       ├── components/
│   │       │   ├── exam-list.tsx
│   │       │   ├── exam-card.tsx
│   │       │   └── exam-detail.tsx
│   │       └── types.ts
│   ├── app/
│   │   └── (dashboard)/
│   │       ├── layout.tsx           # Dashboard layout with auth check
│   │       ├── dashboard/
│   │       │   └── page.tsx         # Dashboard home
│   │       └── exams/
│   │           ├── page.tsx         # Exam list
│   │           └── [examId]/
│   │               └── page.tsx     # Exam detail
│   └── app/
│       └── api/
│           └── exams/
│               └── route.ts         # GET /api/exams
```

**`src/features/exams/services/exam.ts`:**
```ts
export async function getPublishedExams() {
  return prisma.exam.findMany({
    where: { status: "PUBLISHED" },
    include: { sections: { include: { questions: true } } },
    orderBy: { createdAt: "desc" },
  });
}

export async function getExamById(id: string) {
  return prisma.exam.findUnique({
    where: { id },
    include: {
      sections: {
        include: {
          questions: { include: { options: true, answers: true, skills: { include: { skill: true } } } },
          passages: true,
        },
        orderBy: { order: "asc" },
      },
    },
  });
}

export async function getExamTotalPoints(examId: string) {
  const result = await prisma.question.aggregate({
    where: { section: { examId } },
    _sum: { points: true },
  });
  return result._sum.points ?? 0;
}
```

**`src/app/(dashboard)/layout.tsx`:**
```tsx
import { getCurrentUser } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function DashboardLayout({ children }) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return (
    <div className="min-h-screen">
      {/* Sidebar or navbar */}
      <main className="container mx-auto px-4 py-8">{children}</main>
    </div>
  );
}
```

**`src/app/(dashboard)/exams/page.tsx`:** Server component fetching published exams, rendering `<ExamList>`.

**`src/features/exams/components/exam-card.tsx`:** Card showing exam title, type, question count, time limit, "Take Exam" and "Practice" buttons.

**API `GET /api/exams`:** Returns published exams with section/question counts.

**Tests:** None (UI pages).

**Acceptance criteria:**
- Dashboard page loads with auth check
- Exam list shows published exams from seed data
- Exam detail page shows sections, questions, options
- "Take Exam" button links to exam take page
- Responsive layout works

**Dependencies:** T02, T03, T04, T06.

---

## T08: Exam Attempt API & Service

**Goal:** Implement the core exam attempt lifecycle — create, save answers, submit.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── exams/
│   │       └── services/
│   │           └── attempt.ts       # createAttempt, saveAnswer, submitAttempt
│   ├── app/
│   │   └── api/
│   │       └── attempts/
│   │           ├── route.ts          # POST /api/attempts — create attempt
│   │           └── [attemptId]/
│   │               ├── route.ts      # GET /api/attempts/[id] — get attempt
│   │               └── answers/
│   │                   └── route.ts  # PUT /api/attempts/[id]/answers — save answer
│   └── types/
│       └── attempt.ts
```

**`src/features/exams/services/attempt.ts`:**

```ts
export async function createAttempt(profileId, examId, mode) {
  // 1. Verify exam exists and is PUBLISHED
  // 2. Verify exam mode supports the requested mode (BOTH or matching)
  // 3. Check no IN_PROGRESS attempt exists for this user+exam
  // 4. Fetch all questions with options, answers, skills
  // 5. Create ExamAttempt with mode
  // 6. Create QuestionAttempt for each question with questionSnapshot
  // 7. Return attempt with questions
}

export async function saveAnswer(attemptId, profileId, questionId, selectedOptionId?, textAnswer?) {
  // 1. Verify attempt belongs to profile
  // 2. Verify attempt status is IN_PROGRESS
  // 3. Update QuestionAttempt with answer
  // 4. Return updated question attempt
}

export async function submitAttempt(attemptId, profileId) {
  // 1. Verify attempt belongs to profile
  // 2. Verify attempt status is IN_PROGRESS
  // 3. For each QuestionAttempt, grade using scoring engine
  // 4. Create Mistake records for incorrect answers
  // 5. Set attempt status = SUBMITTED, submittedAt = now
  // 6. Return ExamResult
}
```

**`createAttempt` details:**
- Fetch exam with sections → questions → options, answers, skills
- For each question, build `questionSnapshot` JSON:
  ```ts
  {
    id: question.id,
    text: question.text,
    type: question.type,
    instructions: question.instructions,
    points: question.points,
    difficulty: question.difficulty,
    options: question.options.map(o => ({ id: o.id, label: o.label, text: o.text, isCorrect: o.isCorrect })),
    answers: question.answers.map(a => ({ text: a.text, isAcceptable: a.isAcceptable, normalizationRule: a.normalizationRule })),
    skills: question.skills.map(s => ({ name: s.skill.name, category: s.skill.category })),
  }
  ```

**`submitAttempt` details:**
- Load all QuestionAttempts for this attempt
- For each, call `gradeAnswer(snapshot, selectedOptionId, textAnswer, config)`
- Update `isCorrect` and `pointsAwarded`
- If incorrect, create `Mistake` record with category=UNKNOWN (AI classification is Phase 4)
- Compute ExamResult using `calculateExamResult()`

**API routes:**

`POST /api/attempts`:
```ts
// Body: { examId: string, mode: "REAL_EXAM" | "PRACTICE" }
// Auth: requireUser
// Creates attempt, returns attempt with questions
```

`GET /api/attempts/[attemptId]`:
```ts
// Auth: requireUser, verify attempt belongs to user
// Returns attempt with QuestionAttempts
```

`PUT /api/attempts/[attemptId]/answers`:
```ts
// Body: { questionId: string, selectedOptionId?: string, textAnswer?: string }
// Auth: requireUser, verify attempt belongs to user
// Saves answer, returns updated QuestionAttempt
```

**Tests (`tests/unit/exam-attempt.test.ts`):**
```ts
describe("exam attempt", () => {
  test("create attempt creates question attempts with snapshots")
  test("create attempt prevents duplicate IN_PROGRESS attempts")
  test("save answer updates question attempt")
  test("save answer rejects if attempt is submitted")
  test("submit attempt grades all questions")
  test("submit attempt creates mistake records for incorrect answers")
  test("submit attempt sets status to SUBMITTED")
});
```

**Acceptance criteria:**
- Create attempt generates correct number of QuestionAttempts
- questionSnapshot contains all question data
- Save answer persists correctly
- Submit grades all questions deterministically
- Mistake records created for wrong answers
- User cannot save answers to submitted attempt
- User cannot access another user's attempt

**Dependencies:** T02, T05.

---

## T09: Exam-Taking Interface

**Goal:** Build the exam-taking UI with timer, autosave, navigation, and question types.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── exams/
│   │       ├── components/
│   │       │   ├── exam-taker.tsx          # Main exam container
│   │       │   ├── exam-header.tsx         # Title + timer
│   │       │   ├── question-display.tsx    # Renders question by type
│   │       │   ├── question-navigator.tsx  # Grid of question numbers
│   │       │   ├── mc-question.tsx         # Multiple choice renderer
│   │       │   ├── tf-question.tsx         # True/false renderer
│   │       │   ├── short-text-question.tsx # Short text input
│   │       │   ├── fill-blank-question.tsx # Fill in blank
│   │       │   ├── matching-question.tsx   # Matching pairs
│   │       │   ├── writing-question.tsx    # Writing prompt
│   │       │   ├── passage-display.tsx     # Shared passage content
│   │       │   ├── submit-modal.tsx        # Confirmation dialog
│   │       │   └── exam-complete.tsx       # Post-submission redirect
│   │       └── hooks/
│   │           ├── use-exam-timer.ts       # Countdown timer hook
│   │           ├── use-autosave.ts         # Autosave hook
│   │           └── use-exam-state.ts       # Exam state management
│   └── app/
│       └── exam/
│           └── [examId]/
│               └── take/
│                   └── page.tsx            # Exam take page
```

**`src/app/exam/[examId]/take/page.tsx`:**
```tsx
// Server component: fetch attempt or create new one
// If no IN_PROGRESS attempt, create one via API
// Pass attempt data to <ExamTaker> client component
```

**`src/features/exams/components/exam-taker.tsx`:**
```tsx
// Client component managing exam state
// State: currentQuestionIndex, answers (Map<questionId, {selectedOptionId?, textAnswer?}>)
// State: markedForReview (Set<questionId>)
// Renders: ExamHeader (title + timer), QuestionDisplay, QuestionNavigator, Previous/Next buttons
```

**Timer hook (`use-exam-timer.ts`):**
```ts
// Takes: timeLimitMinutes, onSubmit callback
// Returns: { timeRemaining, isRunning, pause, resume }
// Uses: useEffect with setInterval
// On time up: calls onSubmit automatically
// Persists remaining time to localStorage
```

**Autosave hook (`use-autosave.ts`):**
```ts
// Takes: attemptId, answers Map
// Saves to localStorage immediately on change
// Debounces API call every 10 seconds
// On reconnect: syncs queued saves
// Returns: { isSaving, lastSavedAt }
```

**Question display:**
- Switch on question type to render appropriate component
- If question has passage, show `<PassageDisplay>` above question
- MC/TF: Radio button group
- SHORT_TEXT: Text input
- FILL_BLANK: Multiple text inputs (one per blank)
- MATCHING: Drag-and-drop or select-based matching
- WRITING: Textarea

**Question navigator:**
- Grid of question numbers
- Color coding: answered (green), unanswered (gray), marked (amber)
- Click to jump to question

**Submit flow:**
- "Submit" button opens `<SubmitModal>`
- Modal shows: X answered, Y unanswered, Z marked for review
- "Confirm Submit" calls API to submit attempt
- Redirects to results page

**Tests:** None (UI components, manual testing).

**Acceptance criteria:**
- Timer counts down and auto-submits at zero
- Autosave persists to localStorage and syncs to server
- All 6 question types render correctly
- Previous/Next navigation works
- Question navigator shows correct state colors
- Mark for review toggles correctly
- Submit modal shows correct counts
- Submit redirects to results page
- Works on mobile (responsive)

**Dependencies:** T03, T04, T08.

---

## T10: Results Page

**Goal:** Build the post-submission results page with score, section analysis, and question review.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── exams/
│   │       ├── components/
│   │       │   ├── results-page.tsx
│   │       │   ├── score-summary.tsx
│   │       │   ├── section-performance.tsx
│   │       │   ├── question-review.tsx
│   │       │   └── question-review-detail.tsx
│   │       └── services/
│   │           └── results.ts       # getExamResult, getQuestionReview
│   └── app/
│       └── (dashboard)/
│           └── results/
│               └── [attemptId]/
│                   └── page.tsx
```

**`src/features/exams/services/results.ts`:**
```ts
export async function getExamResult(attemptId: string, profileId: string) {
  // 1. Fetch attempt with QuestionAttempts
  // 2. Verify attempt belongs to profile
  // 3. Verify attempt is SUBMITTED or TIME_UP
  // 4. Compute ExamResult from QuestionAttempts
  // 5. Return ExamResult
}

export async function getQuestionReview(attemptId: string, questionId: string, profileId: string) {
  // 1. Fetch QuestionAttempt with questionSnapshot
  // 2. Read from questionSnapshot (NOT current question)
  // 3. Return snapshot + user's answer + correct answer + mistake info
}
```

**`src/features/exams/components/results-page.tsx`:**
- Score Summary: score/total, accuracy%, time
- Section Performance: per-section score with progress bars
- Question Review: clickable list of all questions

**`src/features/exams/components/question-review-detail.tsx`:**
- Question text (from snapshot)
- User's answer (from QuestionAttempt)
- Correct answer (from snapshot)
- Explanation (if available — from Mistake.explanation)
- Skills tested (from snapshot.skills)
- Mistake category (if incorrect)

**`src/app/(dashboard)/results/[attemptId]/page.tsx`:**
- Server component fetching result data
- Renders `<ResultsPage>` component

**Tests:** None (UI pages).

**Acceptance criteria:**
- Score summary shows correct calculation
- Section performance shows per-section breakdown
- Question review shows all questions
- Clicking a question shows detail view
- Correct answer uses snapshot (not current question)
- Unanswered questions shown correctly
- WRITING questions shown as "Not graded"
- Responsive layout

**Dependencies:** T03, T04, T05, T08.

---

## T11: Dashboard Page

**Goal:** Build the dashboard with performance metrics, recent exams, and available exams.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── dashboard/
│   │       ├── components/
│   │       │   ├── dashboard-page.tsx
│   │       │   ├── recent-exam-card.tsx
│   │       │   ├── performance-card.tsx
│   │       │   ├── skill-summary.tsx
│   │       │   ├── recent-mistakes.tsx
│   │       │   └── available-exams.tsx
│   │       └── services/
│   │           └── dashboard.ts     # getDashboardData
│   └── app/
│       └── (dashboard)/
│           └── dashboard/
│               └── page.tsx
```

**`src/features/dashboard/services/dashboard.ts`:**
```ts
export async function getDashboardData(profileId: string) {
  // 1. Recent exam: latest submitted attempt with exam title + score
  // 2. Performance: overall accuracy, exams taken, questions attempted
  // 3. Weakest skills: skill accuracy (computed on demand)
  // 4. Strongest skills: top 3 skills by accuracy
  // 5. Recent mistakes: last 5 mistakes with question text
  // 6. Available exams: published exams with attempt status
}
```

**`src/features/dashboard/services/dashboard.ts` skill accuracy query:**
```ts
export async function getSkillAccuracy(profileId: string) {
  // 1. Get all QuestionAttempts for this profile
  // 2. Join with QuestionSkill to get skills
  // 3. Group by skill, compute accuracy per skill
  // 4. Sort by accuracy ascending (weakest first)
}
```

**Dashboard layout (from spec Section 14.1):**
- Recent Exam card (top left)
- Performance card (top right)
- Weakest Skills card (middle left)
- Strongest Skills card (middle right)
- Recent Mistakes card (bottom left)
- Available Exams card (bottom right)

**Tests:** None (UI pages).

**Acceptance criteria:**
- Dashboard loads with all 6 cards
- Recent exam shows latest attempt
- Performance shows correct accuracy
- Skills sorted correctly (weakest/strongest)
- Recent mistakes show question text
- Available exams show "Take Exam" / "Practice" buttons
- Empty states shown when no data

**Dependencies:** T04, T07, T08, T10.

---

# PHASE 2 — Question Bank & Practice (Tasks T12–T17)

---

## T12: Question Bank Service & API

**Goal:** Implement question bank queries with filtering and search.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── questions/
│   │       ├── services/
│   │       │   └── question-bank.ts
│   │       └── types.ts
│   └── app/
│       └── api/
│           └── questions/
│               └── route.ts          # GET /api/questions — filtered question list
```

**`src/features/questions/services/question-bank.ts`:**
```ts
export async function getQuestionBank(filters: QuestionBankFilters) {
  // filters: { examId?, sectionId?, skillId?, type?, difficulty?, search?, page?, limit? }
  // Query Question with includes: section, options, answers, skills, exam
  // Apply WHERE conditions based on filters
  // Apply pagination
  // Return { questions, total, page, limit }
}

export async function getQuestionBankStats() {
  // Total questions, per-type count, per-skill count
}
```

**`GET /api/questions`:**
```ts
// Query params: examId, sectionId, skillId, type, difficulty, search, page, limit
// Auth: requireUser
// Returns paginated questions with metadata
```

**Tests:** None (service only, tested via integration).

**Acceptance criteria:**
- Filter by exam works
- Filter by section works
- Filter by skill works
- Filter by type works
- Search by text works
- Pagination works
- Returns total count for pagination UI

**Dependencies:** T02.

---

## T13: Question Bank UI

**Goal:** Build the question bank browsing interface with filters and search.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── questions/
│   │       └── components/
│   │           ├── question-bank-page.tsx
│   │           ├── question-filters.tsx
│   │           ├── question-list.tsx
│   │           └── question-card.tsx
│   └── app/
│       └── (dashboard)/
│           └── question-bank/
│               └── page.tsx
```

**`question-filters.tsx`:**
- Search input
- Exam dropdown (All + specific exams)
- Section dropdown
- Skill dropdown (hierarchical)
- Type dropdown (All, MC, TF, etc.)
- Difficulty dropdown

**`question-card.tsx`:**
- Question number, type badge, difficulty
- Question text (truncated)
- Exam source, skill tags
- Usage count (from QuestionAttempt)

**Tests:** None (UI).

**Acceptance criteria:**
- All filters work independently
- Filters combine correctly
- Search updates results
- Pagination works
- Empty state when no results

**Dependencies:** T03, T04, T12.

---

## T14: Practice Session Service & API

**Goal:** Implement practice session creation and management.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── practice/
│   │       ├── services/
│   │       │   └── practice.ts
│   │       └── types.ts
│   └── app/
│       └── api/
│           └── practice/
│               └── route.ts          # POST /api/practice — create practice session
```

**`src/features/practice/services/practice.ts`:**
```ts
export async function createPracticeSession(profileId: string, config: PracticeConfig) {
  // config: { questionCount, skillId?, difficulty?, type? }
  // 1. Query QuestionBank for matching questions
  // 2. Randomly select questionCount questions
  // 3. Create a "practice exam" (Exam with status=DRAFT, mode=PRACTICE)
  // 4. Create ExamAttempt with mode=PRACTICE
  // 5. Create QuestionAttempts with snapshots
  // 6. Return attempt
}

export async function createMistakePracticeSession(profileId: string, questionCount: number) {
  // 1. Get user's recent Mistakes (last N)
  // 2. Extract unique questionIds
  // 3. Select questionCount from those
  // 4. Create practice session (same as above)
}
```

**PracticeConfig type:**
```ts
interface PracticeConfig {
  questionCount: number;      // default 10
  skillId?: string;
  difficulty?: string;
  type?: QuestionType;
}
```

**`POST /api/practice`:**
```ts
// Body: PracticeConfig
// Auth: requireUser
// Creates practice session, returns attempt with questions
```

**Tests:** None.

**Acceptance criteria:**
- Creates practice attempt with correct number of questions
- Filters work (skill, difficulty, type)
- Mistake practice selects from recent mistakes
- Practice attempt mode = PRACTICE

**Dependencies:** T02, T08, T12.

---

## T15: Practice Mode UI

**Goal:** Build the practice mode interface with immediate feedback and AI explanations.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── practice/
│   │       ├── components/
│   │       │   ├── practice-setup.tsx       # Configure practice session
│   │       │   ├── practice-taker.tsx       # Practice session interface
│   │       │   ├── practice-feedback.tsx    # Immediate feedback after answer
│   │       │   └── ai-explanation.tsx       # AI explanation panel
│   │       └── hooks/
│   │           └── use-practice.ts
│   └── app/
│       └── (dashboard)/
│           └── practice/
│               ├── page.tsx                 # Practice setup page
│               └── [attemptId]/
│                   └── page.tsx             # Practice session page
```

**`practice-setup.tsx`:**
- Question count input
- Skill filter
- Difficulty filter
- Type filter
- "Practice My Mistakes" button
- "Start Practice" button

**`practice-taker.tsx`:**
- Similar to exam-taker but with:
  - No timer (optional)
  - After answering, show feedback immediately
  - "Explain this question" button for wrong answers
  - "Next" button moves to next question
  - No submit modal — auto-advances

**`practice-feedback.tsx`:**
- Shows: correct/incorrect, user answer, correct answer
- If incorrect: shows explanation (from Mistake or AI)
- "Explain this question" button triggers AI

**`ai-explanation.tsx`:**
- Calls `POST /api/ai/explain` with question data
- Shows AI explanation in loading → loaded states
- Explanation includes: why correct, why wrong, French context, takeaway

**Tests:** None (UI).

**Acceptance criteria:**
- Practice setup creates session correctly
- Immediate feedback shown after answering
- Correct answer revealed
- AI explanation loads and displays
- Navigation works (prev/next)
- "Practice My Mistakes" works

**Dependencies:** T03, T04, T09, T14.

---

## T16: Mistake Tracking

**Goal:** Implement mistake tracking service and mistake review UI.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── exams/
│   │       ├── services/
│   │       │   └── mistakes.ts        # getMistakes, getMistakeStats
│   │       └── components/
│   │           ├── mistakes-page.tsx
│   │           ├── mistake-list.tsx
│   │           └── mistake-card.tsx
│   └── app/
│       └── (dashboard)/
│           └── mistakes/
│               └── page.tsx
```

**`src/features/exams/services/mistakes.ts`:**
```ts
export async function getMistakes(profileId: string, filters?: MistakeFilters) {
  // Fetch Mistakes with questionSnapshot, question, exam attempt
  // Filter by category, skill, date range
  // Paginate
}

export async function getMistakeStats(profileId: string) {
  // Mistake frequency by category
  // Mistakes over time
  // Top mistake skills
}

export async function updateMistakeCategory(mistakeId: string, profileId: string, category: MistakeCategory) {
  // User can override AI classification
  // Verify mistake belongs to profile
}
```

**Mistakes page:**
- List of recent mistakes
- Filter by category, skill, date
- Click to see full question + answer details
- "Override category" dropdown

**Tests:** None.

**Acceptance criteria:**
- Mistakes page shows all user mistakes
- Filters work
- Category override works
- Statistics computed correctly
- Empty state when no mistakes

**Dependencies:** T02, T04, T08.

---

## T17: Performance Statistics

**Goal:** Implement aggregate performance queries for the dashboard.

**Files to create:**
```
french-exam-trainer/
├── src/
│   └── features/
│       └── dashboard/
│           └── services/
│               └── stats.ts           # computePerformanceStats
```

**`src/features/dashboard/services/stats.ts`:**
```ts
export async function computePerformanceStats(profileId: string) {
  // 1. Overall accuracy: total correct / total attempted
  // 2. Recent accuracy: last 50 question attempts
  // 3. Skill accuracy: per-skill breakdown
  // 4. Mistake frequency: per-category count
  // 5. Exam history: list of attempts with scores
  // 6. Improvement trend: accuracy over time (last 10 exams)
}
```

**Queries needed:**
```ts
// Overall accuracy
const totalAttempts = await prisma.questionAttempt.count({ where: { attempt: { profileId } } });
const correctAttempts = await prisma.questionAttempt.count({ where: { attempt: { profileId }, isCorrect: true } });
const accuracy = totalAttempts > 0 ? correctAttempts / totalAttempts : 0;

// Skill accuracy
const skillStats = await prisma.questionAttempt.groupBy({
  by: ["questionId"],
  where: { attempt: { profileId }, isCorrect: { not: null } },
  _count: { id: true },
  _sum: { pointsAwarded: true },
});
// Join with QuestionSkill to get skill-level aggregation
```

**Tests:** None (service only).

**Acceptance criteria:**
- Overall accuracy computed correctly
- Recent accuracy excludes older attempts
- Skill accuracy computed per skill
- Mistake frequency by category
- Exam history sorted by date

**Dependencies:** T02, T08.

---

# PHASE 3 — Exam Import (Tasks T18–T22)

---

## T18: Document Upload & Storage

**Goal:** Implement file upload to Supabase Storage with validation.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── lib/
│   │   └── storage.ts               # Supabase storage client
│   ├── features/
│   │   └── imports/
│   │       ├── services/
│   │       │   └── upload.ts         # uploadDocument
│   │       └── types.ts
│   └── app/
│       └── api/
│           └── imports/
│               └── upload/
│                   └── route.ts      # POST /api/imports/upload
```

**`src/lib/storage.ts`:**
```ts
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function uploadFile(buffer: Buffer, path: string, contentType: string) {
  const { data, error } = await supabase.storage
    .from("exam-documents")
    .upload(path, buffer, { contentType, upsert: false });
  if (error) throw error;
  return data;
}

export async function getFileUrl(path: string) {
  const { data } = await supabase.storage.from("exam-documents").createSignedUrl(path, 3600);
  return data?.signedUrl;
}
```

**`src/features/imports/services/upload.ts`:**
```ts
export async function uploadDocument(file: File, profileId: string) {
  // 1. Validate file type: PDF, JPG, JPEG, PNG
  // 2. Validate file size: < 50MB
  // 3. Generate storage path: `{profileId}/{timestamp}-{filename}`
  // 4. Upload to Supabase Storage
  // 5. Create Document record in DB
  // 6. Create ContentImport record
  // 7. Return Document + ContentImport
}
```

**`POST /api/imports/upload`:**
```ts
// Multipart form data
// Auth: requireAdmin
// Validates file type and size
// Uploads to storage
// Creates Document + ContentImport
// Returns created records
```

**Tests:** None.

**Acceptance criteria:**
- PDF upload works
- Image upload works
- File size validation (reject > 50MB)
- File type validation (reject non-PDF/image)
- Document record created
- ContentImport record created
- File accessible via Supabase Storage

**Dependencies:** T02, T04.

---

## T19: PDF Extraction & OCR

**Goal:** Implement PDF text extraction with OCR fallback for scanned documents.

**Files to create:**
```
french-exam-trainer/
├── src/
│   └── lib/
│       └── pdf/
│           ├── extractor.ts          # extractTextFromPDF
│           └── ocr.ts                # extractTextFromImage
```

**`src/lib/pdf/extractor.ts`:**
```ts
import pdfParse from "pdf-parse";

export interface ExtractionResult {
  text: string;
  pageCount: number;
  hasSelectableText: boolean;
  pages: Array<{ pageNumber: number; text: string }>;
}

export async function extractTextFromPDF(buffer: Buffer): Promise<ExtractionResult> {
  const data = await pdfParse(buffer);
  const pages = data.numpages > 0
    ? Array.from({ length: data.numpages }, (_, i) => ({ pageNumber: i + 1, text: "" }))
    : [];

  // pdf-parse doesn't give per-page text directly in v1
  // For V1, treat entire document as one text block
  const hasSelectableText = data.text.trim().length > 50;

  return {
    text: data.text,
    pageCount: data.numpages,
    hasSelectableText,
    pages,
  };
}
```

**`src/lib/pdf/ocr.ts`:**
```ts
import Tesseract from "tesseract.js";

export interface OCRResult {
  text: string;
  confidence: number;
  pages: Array<{ pageNumber: number; text: string; confidence: number }>;
}

export async function extractTextFromImage(imageBuffer: Buffer): Promise<OCRResult> {
  const result = await Tesseract.recognize(imageBuffer, "fra+eng");
  return {
    text: result.data.text,
    confidence: result.data.confidence / 100,
    pages: [{ pageNumber: 1, text: result.data.text, confidence: result.data.confidence / 100 }],
  };
}

export async function extractTextFromScannedPDF(buffer: Buffer, pageCount: number): Promise<OCRResult> {
  // For V1: convert PDF pages to images using pdf-to-image or similar
  // Then OCR each page
  // This is complex — for V1, we can skip this and require text-based PDFs
  // or images
  throw new Error("Scanned PDF OCR not implemented in V1. Use text-based PDF or images.");
}
```

**Integration with ContentImport pipeline:**
```ts
// In upload service or separate processing service:
export async function processExtraction(importId: string) {
  // 1. Fetch ContentImport + Document
  // 2. Download file from Supabase Storage
  // 3. If PDF: extractTextFromPDF
  //    If image: extractTextFromImage
  // 4. Update ContentImport: extractionStatus = COMPLETED
  // 5. Store extracted text (in ContentImport or separate)
  // 6. If no selectable text and PDF: set ocrStatus = RUNNING, attempt OCR
}
```

**Tests (`tests/unit/import-parsing.test.ts`):**
```ts
describe("PDF extraction", () => {
  test("extracts text from text-based PDF")
  test("detects low text content")
  test("handles invalid PDF gracefully")
});

describe("OCR extraction", () => {
  test("extracts text from image")
  test("returns confidence score")
});
```

**Acceptance criteria:**
- Text-based PDF extraction works
- Image OCR works with French text
- Low text detection triggers OCR path
- Invalid PDF handled gracefully
- Extraction result stored in ContentImport

**Dependencies:** T02, T18.

---

## T20: AI Exam Parser

**Goal:** Implement AI provider abstraction and exam parsing with Zod validation.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── lib/
│   │   └── ai/
│   │       ├── types.ts              # AIProvider interface
│   │       ├── provider.ts           # getAIProvider()
│   │       └── gemini.ts             # Gemini implementation
│   ├── services/
│   │   └── exam-parser.ts            # parseExamWithAI
│   └── lib/
│       └── validation/
│           └── schemas.ts            # ParsedExamSchema (Zod)
```

**`src/lib/ai/types.ts`:**
```ts
export interface AIProvider {
  parseExam(text: string, context: ParseContext): Promise<ParsedExam>;
  classifyMistake(params: ClassifyMistakeParams): Promise<MistakeClassification>;
  explainQuestion(params: ExplainQuestionParams): Promise<Explanation>;
}

export interface ParseContext {
  filename: string;
  pageCount?: number;
  language?: string;
}

export interface ClassifyMistakeParams {
  questionText: string;
  options?: Array<{ label: string; text: string }>;
  correctAnswer: string;
  userAnswer: string;
  skills?: string[];
}

export interface MistakeClassification {
  category: string;
  confidence: number;
  explanation?: string;
}

export interface ExplainQuestionParams {
  questionText: string;
  options?: Array<{ label: string; text: string }>;
  correctAnswer: string;
  userAnswer: string;
  skills?: string[];
}

export interface Explanation {
  whyCorrect: string;
  whyIncorrect: string;
  frenchContext: string;
  takeaway: string;
}
```

**`src/lib/validation/schemas.ts`:**
```ts
import { z } from "zod";

export const ParsedExamSchema = z.object({
  title: z.string(),
  type: z.string().optional(),
  year: z.number().optional(),
  timeLimitMinutes: z.number().optional(),
  totalPoints: z.number().optional(),
  sections: z.array(z.object({
    title: z.string(),
    instructions: z.string().optional(),
    passages: z.array(z.object({
      title: z.string().optional(),
      content: z.string(),
      type: z.enum(["READING_TEXT", "AUDIO_TRANSCRIPT", "IMAGE", "OTHER"]),
    })).optional(),
    questions: z.array(z.object({
      number: z.number(),
      type: z.enum(["MULTIPLE_CHOICE", "TRUE_FALSE", "SHORT_TEXT", "FILL_BLANK", "MATCHING", "WRITING"]),
      text: z.string(),
      instructions: z.string().optional(),
      passageIndex: z.number().optional(),
      options: z.array(z.object({
        label: z.string(),
        text: z.string(),
      })).optional(),
      correctAnswer: z.union([z.string(), z.array(z.string())]).optional(),
      points: z.number().optional(),
      difficulty: z.string().optional(),
    })),
  })),
});

export type ParsedExam = z.infer<typeof ParsedExamSchema>;
```

**`src/lib/ai/gemini.ts`:**
```ts
import { GoogleGenerativeAI } from "@google/generative-ai";
import { type AIProvider, type ParseContext, type ParsedExam, type ClassifyMistakeParams, type MistakeClassification, type ExplainQuestionParams, type Explanation } from "./types";
import { ParsedExamSchema } from "@/lib/validation/schemas";

export class GeminiProvider implements AIProvider {
  private genAI: GoogleGenerativeAI;

  constructor() {
    this.genAI = new GoogleGenerativeAI(process.env.GOOGLE_AI_API_KEY!);
  }

  async parseExam(text: string, context: ParseContext): Promise<ParsedExam> {
    const model = this.genAI.getGenerativeModel({ model: "gemini-2.0-flash" });
    const prompt = `You are an expert French exam parser. Extract the following exam into structured JSON...
    [detailed prompt with examples]
    Return ONLY valid JSON matching this schema: ${JSON.stringify(ParsedExamSchema.shape)}`;

    const result = await model.generateContent([prompt, text]);
    const response = result.response.text();
    const parsed = JSON.parse(response);
    return ParsedExamSchema.parse(parsed); // Zod validation
  }

  async classifyMistake(params: ClassifyMistakeParams): Promise<MistakeClassification> {
    // Similar pattern with Zod validation
  }

  async explainQuestion(params: ExplainQuestionParams): Promise<Explanation> {
    // Similar pattern with Zod validation
  }
}
```

**`src/lib/ai/provider.ts`:**
```ts
import { GeminiProvider } from "./gemini";
import type { AIProvider } from "./types";

let provider: AIProvider | null = null;

export function getAIProvider(): AIProvider {
  if (!provider) {
    provider = new GeminiProvider();
  }
  return provider;
}
```

**`src/services/exam-parser.ts`:**
```ts
export async function parseExamWithAI(importId: string) {
  // 1. Fetch ContentImport + extracted text
  // 2. Get AI provider
  // 3. Call parseExam with extracted text
  // 4. Validate response with Zod (already done in provider)
  // 5. Update ContentImport: aiParsingStatus = COMPLETED, aiConfidence
  // 6. Return ParsedExam
}
```

**Tests (`tests/unit/import-parsing.test.ts`):**
```ts
describe("AI exam parser", () => {
  test("validates correct JSON structure")
  test("rejects malformed JSON")
  test("rejects missing required fields")
  test("handles missing answer key gracefully")
  test("validates question types against enum")
});
```

**Acceptance criteria:**
- AIProvider interface implemented by GeminiProvider
- Zod validation catches malformed output
- parseExam returns structured ParsedExam
- Classification returns category + confidence
- Explanation returns 4 sections
- Provider is swappable via config

**Dependencies:** T02.

---

## T21: Import Review UI

**Goal:** Build the admin import review interface for editing and approving extracted exams.

**Files to create:**
```
french-exam-trainer/
├── src/
│   ├── features/
│   │   └── imports/
│   │       ├── services/
│   │       │   └── import.ts         # getImports, approveImport, rejectImport
│   │       ├── components/
│   │       │   ├── import-list.tsx
│   │       │   ├── import-detail.tsx
│   │       │   ├── import-review.tsx
│   │       │   ├── extracted-question.tsx
│   │       │   ├── edit-question-dialog.tsx
│   │       │   └── import-status-badge.tsx
│   │       └── types.ts
│   ├── app/
│   │   ├── api/
│   │   │   └── imports/
│   │   │       ├── route.ts          # GET /api/imports — list imports
│   │   │       └── [importId]/
│   │   │           ├── route.ts      # GET /api/imports/[id] — get import detail
│   │   │           ├── approve/
│   │   │           │   └── route.ts  # POST /api/imports/[id]/approve
│   │   │           ├── reject/
│   │   │           │   └── route.ts  # POST /api/imports/[id]/reject
│   │   │           └── retry/
│   │   │               └── route.ts  # POST /api/imports/[id]/retry
│   │   └── (dashboard)/
│   │       └── imports/
│   │           ├── page.tsx          # Import list
│   │           └── [importId]/
│   │               └── page.tsx      # Import detail + review
│   └── admin/
│       ├── layout.tsx                # Admin layout with role check
│       ├── imports/
│       │   └── page.tsx
│       └── exams/
│           └── page.tsx
```

**`src/features/imports/services/import.ts`:**
```ts
export async function getImports(profileId: string) {
  // Fetch ContentImports with document info
  // Admin sees all, user sees own
}

export async function getImportDetail(importId: string, profileId: string) {
  // Fetch import with parsed exam data
  // Return sections, questions, options from parsed JSON
}

export async function approveImport(importId: string, profileId: string) {
  // 1. Verify admin role
  // 2. Fetch import with parsed data
  // 3. Create Exam (DRAFT → PUBLISHED)
  // 4. Create ExamSections
  // 5. Create Questions with Options, Answers, Skills
  // 6. Create ExamSource linking Document
  // 7. Update import status
  // 8. Return created Exam
}

export async function rejectImport(importId: string, profileId: string, reason?: string) {
  // 1. Verify admin role
  // 2. Update import status to REJECTED
  // 3. Optionally store rejection reason
}

export async function retryImportStep(importId: string, step: "extraction" | "ocr" | "ai_parsing") {
  // 1. Verify admin role
  // 2. Reset the failed step to PENDING
  // 3. Re-run that step only
}
```

**`src/admin/layout.tsx`:**
```tsx
import { requireAdmin } from "@/lib/auth";
import { redirect } from "next/navigation";

export default async function AdminLayout({ children }) {
  try {
    await requireAdmin();
  } catch {
    redirect("/dashboard");
  }
  return <div>{children}</div>;
}
```

**Import review page:**
- Shows parsed exam data (sections, questions, options)
- Each question shows confidence score
- Low-confidence items flagged with warning
- Edit button opens edit dialog
- Delete button removes question
- Add question button
- Approve/Reject buttons at top

**Edit question dialog:**
- Edit question text
- Edit options (add/remove/edit)
- Edit correct answer
- Edit points
- Edit skills

**Tests:** None (UI).

**Acceptance criteria:**
- Import list shows all imports
- Import detail shows parsed data
- Low-confidence items flagged
- Edit question works
- Approve creates exam with all records
- Reject marks import as rejected
- Retry re-runs failed step
- Only admins can approve/reject

**Dependencies:** T03, T04, T18, T19, T20.

---

## T22: Import Pipeline Orchestration

**Goal:** Wire together the complete import pipeline: upload → extract → AI parse → review → approve.

**Files to create/modify:**
```
french-exam-trainer/
├── src/
│   └── features/
│       └── imports/
│           ├── services/
│           │   └── pipeline.ts       # runImportPipeline
│           └── components/
│               ├── upload-zone.tsx    # Drag & drop upload
│               └── import-progress.tsx # Progress indicator
```

**`src/features/imports/services/pipeline.ts`:**
```ts
export async function runImportPipeline(importId: string) {
  // Step 1: Extraction
  await updateImportStep(importId, "extraction", "RUNNING");
  try {
    const extraction = await extractText(importId);
    await updateImportStep(importId, "extraction", "COMPLETED");
  } catch (error) {
    await updateImportStep(importId, "extraction", "FAILED", error.message);
    return; // Stop pipeline
  }

  // Step 1b: OCR (if needed)
  if (needsOCR(extraction)) {
    await updateImportStep(importId, "ocr", "RUNNING");
    try {
      const ocr = await runOCR(importId);
      await updateImportStep(importId, "ocr", "COMPLETED");
    } catch (error) {
      await updateImportStep(importId, "ocr", "FAILED", error.message);
      return;
    }
  }

  // Step 2: AI Parsing
  await updateImportStep(importId, "ai_parsing", "RUNNING");
  try {
    const parsed = await parseExamWithAI(importId);
    await updateImportStep(importId, "ai_parsing", "COMPLETED");
  } catch (error) {
    await updateImportStep(importId, "ai_parsing", "FAILED", error.message);
    return;
  }

  // Pipeline complete — import ready for review
  await updateImportStatus(importId, "COMPLETED");
}
```

**`upload-zone.tsx`:**
- Drag & drop area
- Click to browse
- File type validation (PDF, JPG, JPEG, PNG)
- File size validation (< 50MB)
- Upload progress indicator
- Success/error feedback

**`import-progress.tsx`:**
- Step 1: Text Extraction — status indicator
- Step 1b: OCR — status indicator (shown if needed)
- Step 2: AI Parsing — status indicator
- Step 3: Ready for Review — status indicator
- Each step shows: pending, running (spinner), completed (check), failed (X)

**Tests:** None (integration).

**Acceptance criteria:**
- Upload triggers pipeline automatically
- Pipeline runs steps sequentially
- Failed step stops pipeline
- Retry re-runs only failed step
- Progress indicator updates in real-time
- Import ready for review after pipeline completes
- Admin can approve from review page

**Dependencies:** T18, T19, T20, T21.

---

## Post-Implementation

### Run All Tests
```bash
npm run test
npm run lint
npx tsc --noEmit
npm run build
```

### Verify End-to-End Flow

**Admin flow:**
1. Login as admin
2. Navigate to Import Exam
3. Upload a PDF
4. Watch pipeline progress
5. Review extracted questions
6. Edit any incorrect extraction
7. Approve import
8. Exam appears in Published Exams

**User flow:**
1. Login as student
2. See dashboard with demo exam
3. Click "Take Exam" on demo exam
4. Answer questions with timer
5. Submit exam
6. See score, section analysis, question review
7. Navigate to Question Bank
8. Filter by skill
9. Start practice session
10. Get immediate feedback
11. Click "Explain this question" for wrong answers
12. View mistakes page

### Seed Admin User
After deployment, create admin user:
```sql
-- Via Supabase dashboard or API
INSERT INTO "Profile" (id, email, role) VALUES ('<auth-user-id>', 'admin@example.com', 'ADMIN');
```

---

## Task Dependency Summary

```
T01 (Scaffolding)
  └→ T02 (Schema)
      ├→ T03 (UI Components) ─────────────────────────┐
      ├→ T05 (Scoring Engine)                         │
      ├→ T06 (Seed Data)                              │
      ├→ T12 (Question Bank Service)                  │
      ├→ T18 (Upload & Storage)                       │
      └→ T20 (AI Parser)                              │
                                                      │
T02 + T03 + T04 (Auth) ──────────────────────────────→│
  └→ T07 (Exam List/Detail) ──────────────────────────→│
      └→ T08 (Attempt API) ──────────────────────────→│
          ├→ T09 (Exam-Taking UI)                     │
          ├→ T14 (Practice Service)                   │
          └→ T16 (Mistakes)                           │
                                                      │
T05 + T08 → T10 (Results Page)                        │
T04 + T07 + T08 + T10 → T11 (Dashboard)              │
T03 + T12 → T13 (Question Bank UI)                   │
T03 + T08 + T14 → T15 (Practice UI)                  │
T02 + T08 → T17 (Performance Stats)                  │
T18 + T19 → T20 + T21 (Import Review) ──────────────→│
T18 + T19 + T20 + T21 → T22 (Pipeline Orchestration) │
                                                      │
Final: npm run test && npm run lint && npm run build ─┘
```
