# French Exam Trainer — Design Specification

**Date:** 2026-09-03
**Scope:** Phase 1-3 (Core Exam Engine, Question Bank, Exam Import)
**Status:** Approved for implementation

---

## 1. Product Overview

A French exam practice platform where users upload exam papers as PDF/images, AI parses and structures them, users take exams online, the system automatically grades objective questions, and analyzes performance and mistakes.

This is NOT a web search engine. The user manually uploads exam files. The system prioritizes the exam-taking experience and exam data engine, with an exam import/AI parsing module as a supporting feature.

### Core Workflows

**Admin Workflow:**
```
Upload PDF → AI parses exam → Review extracted questions → Fix errors → Approve → Publish
```

**User Exam Workflow:**
```
Open Exams → Select exam → Start exam → Answer questions → Timer + autosave → Submit → Score → Section analysis → Question review → Mistake tracking → Performance history
```

**User Practice Workflow:**
```
Question Bank → Choose practice → Answer questions → Immediate feedback → AI explanation → Mistake saved
```

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js (App Router) |
| Language | TypeScript |
| UI | React + Tailwind CSS + shadcn/ui |
| Database | PostgreSQL (Supabase) |
| ORM | Prisma |
| Auth | Supabase Auth |
| File Storage | Supabase Storage |
| Validation | Zod |
| PDF Processing | pdf-parse + Tesseract.js (OCR) |
| AI | Multi-provider abstraction (default: Google Gemini) |
| Testing | Vitest |

---

## 3. Architecture

### 3.1 Project Structure

```
french-exam-trainer/
├── src/
│   ├── app/                          # Next.js app router pages
│   │   ├── (auth)/                   # Auth routes (login, register)
│   │   ├── (dashboard)/              # Dashboard layout group
│   │   │   ├── dashboard/
│   │   │   ├── exams/
│   │   │   ├── question-bank/
│   │   │   ├── results/
│   │   │   ├── imports/
│   │   │   └── settings/
│   │   ├── exam/
│   │   │   └── [examId]/
│   │   │       └── take/             # Exam-taking interface
│   │   ├── admin/
│   │   │   ├── imports/
│   │   │   ├── exams/
│   │   │   └── questions/
│   │   ├── api/                      # API routes
│   │   │   ├── exams/
│   │   │   ├── attempts/
│   │   │   ├── questions/
│   │   │   ├── imports/
│   │   │   ├── ai/
│   │   │   └── admin/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── features/
│   │   ├── exams/                    # Exam CRUD, attempt management, scoring
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   ├── hooks/
│   │   │   └── types.ts
│   │   ├── questions/                # Question bank, types, skills
│   │   ├── imports/                  # Upload, AI parsing, review
│   │   ├── practice/                 # Practice sessions
│   │   └── dashboard/               # Performance, stats, charts
│   ├── shared/
│   │   ├── ui/                       # shadcn components
│   │   ├── lib/                      # Utilities (cn, formatDate, etc.)
│   │   └── types/                    # Shared TypeScript types
│   ├── lib/
│   │   ├── db/                       # Prisma client singleton
│   │   ├── ai/                       # AI provider abstraction
│   │   ├── storage/                  # Supabase storage client
│   │   └── pdf/                      # PDF parsing + OCR
│   ├── services/                     # Domain services
│   │   ├── scoring.ts                # Deterministic scoring engine
│   │   ├── exam-parser.ts            # AI exam parsing orchestration
│   │   ├── mistake-analyzer.ts       # Mistake classification
│   │   └── explanation-generator.ts  # AI question explanations
│   └── types/                        # Global type definitions
├── prisma/
│   ├── schema.prisma
│   ├── migrations/
│   └── seed/
│       └── seed.ts                   # Demo data
├── public/
├── tests/
│   ├── unit/
│   │   ├── scoring.test.ts
│   │   ├── exam-attempt.test.ts
│   │   └── import-parsing.test.ts
│   └── integration/
├── docs/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
└── .env.local
```

### 3.2 Separation of Concerns

```
UI (React components)
    ↓
Application Services (API routes)
    ↓
Domain Logic (scoring, exam state, mistake classification)
    ↓
Repositories (Prisma queries)
    ↓
Database (PostgreSQL via Supabase)
```

AI is an infrastructure/service layer, not mixed into React components.

### 3.3 AI Provider Abstraction

```typescript
interface AIProvider {
  parseExam(document: UploadedDocument, context: ParseContext): Promise<ParsedExam>;
  classifyMistake(params: ClassifyMistakeParams): Promise<MistakeClassification>;
  explainQuestion(params: ExplainQuestionParams): Promise<Explanation>;
}
```

Providers implement this interface. The application imports a provider instance, never a concrete class directly. Switching providers requires only changing the provider configuration.

---

## 4. Database Schema (Prisma)

### 4.1 Core Entities

#### Profile
```prisma
model Profile {
  id          String   @id @default(uuid()) // references Supabase auth.users.id
  displayName String?
  email       String   @unique
  role        Role     @default(STUDENT)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  examAttempts   ExamAttempt[]
  mistakes       Mistake[]
}
// Cascade: Profile delete → cascade delete ExamAttempt, Mistake
```

#### Exam
```prisma
model Exam {
  id               String     @id @default(uuid())
  title            String
  description      String?
  type             String?    // DELF B2, HSGQG, etc. — flexible, not enum
  year             Int?
  language         String     @default("fr")
  timeLimitMinutes Int?
  totalPoints      Int?       // null = computed from questions at query time
  negativePoints   Int        @default(0)
  mode             ExamMode   @default(BOTH)
  status           ExamStatus @default(DRAFT)
  createdAt        DateTime   @default(now())
  updatedAt        DateTime   @updatedAt

  sections         ExamSection[]
  attempts         ExamAttempt[]
  sources          ExamSource[]
  imports          ContentImport[]
}
// Cascade: Exam delete → cascade delete ExamSection, ExamAttempt, ExamSource, ContentImport
```

#### ExamSection
```prisma
model ExamSection {
  id           String   @id @default(uuid())
  examId       String
  title        String
  instructions String?
  order        Int
  createdAt    DateTime @default(now())

  exam      Exam       @relation(fields: [examId], references: [id])
  passages  Passage[]
  questions Question[]

  @@index([examId])
}
// Cascade: ExamSection delete → cascade delete Passage, Question
```

#### Passage
```prisma
model Passage {
  id         String       @id @default(uuid())
  sectionId  String
  title      String?
  content    String       // Reading text, transcript, or description
  type       PassageType
  sourcePage Int?
  createdAt  DateTime     @default(now())

  section   ExamSection @relation(fields: [sectionId], references: [id])
  questions Question[]

  @@index([sectionId])
}
// Cascade: Passage delete → Restrict (questions reference it)
```

#### Question
```prisma
model Question {
  id          String       @id @default(uuid())
  sectionId   String
  passageId   String?
  number      Int
  type        QuestionType
  text        String
  instructions String?
  points      Int          @default(1)
  difficulty  String?      // B1, B2, C1, etc. — flexible
  order       Int
  sourcePage  Int?
  createdAt   DateTime     @default(now())

  section   ExamSection      @relation(fields: [sectionId], references: [id])
  passage   Passage?         @relation(fields: [passageId], references: [id])
  options   QuestionOption[]
  answers   QuestionAnswer[]
  skills    QuestionSkill[]
  attempts  QuestionAttempt[]
  versions  QuestionVersion[]

  @@index([sectionId])
  @@index([passageId])
}
// Cascade: Question delete → cascade delete QuestionOption, QuestionAnswer,
//           QuestionSkill, QuestionVersion. Restrict on QuestionAttempt (preserve history).
```

#### QuestionOption
```prisma
model QuestionOption {
  id         String   @id @default(uuid())
  questionId String
  label      String   // A, B, C, D, etc.
  text       String
  isCorrect  Boolean  @default(false)

  question   Question           @relation(fields: [questionId], references: [id])
  selectedIn QuestionAttempt[]

  @@index([questionId])
}
// Cascade: QuestionOption delete → Restrict if QuestionAttempt references it (preserve history)
```

#### QuestionAnswer
```prisma
model QuestionAnswer {
  id               String   @id @default(uuid())
  questionId       String
  text             String
  isAcceptable     Boolean  @default(true)
  normalizationRule Json?   // { trimWhitespace, caseInsensitive, removeAccents, etc. }

  question Question @relation(fields: [questionId], references: [id])

  @@index([questionId])
}
// Cascade: QuestionAnswer delete → cascade with Question
```

#### Skill
```prisma
model Skill {
  id       String  @id @default(uuid())
  name     String
  parentId String?
  category String?

  parent   Skill?          @relation("SkillHierarchy", fields: [parentId], references: [id])
  children Skill[]         @relation("SkillHierarchy")
  questions QuestionSkill[]

  @@index([parentId])
}
// Cascade: Skill delete → set null on children.parentId, Restrict on QuestionSkill
```

#### QuestionSkill
```prisma
model QuestionSkill {
  id         String @id @default(uuid())
  questionId String
  skillId    String

  question Question @relation(fields: [questionId], references: [id])
  skill    Skill    @relation(fields: [skillId], references: [id])

  @@unique([questionId, skillId])
}
// Cascade: cascade with Question or Skill deletion
```

### 4.2 Exam Attempt Entities

#### ExamAttempt
```prisma
model ExamAttempt {
  id               String       @id @default(uuid())
  profileId        String
  examId           String
  status           AttemptStatus @default(IN_PROGRESS)
  mode             AttemptMode   // REAL_EXAM or PRACTICE — which mode was used
  startedAt        DateTime     @default(now())
  submittedAt      DateTime?
  timeSpentSeconds Int          @default(0)

  profile   Profile          @relation(fields: [profileId], references: [id])
  exam      Exam             @relation(fields: [examId], references: [id])
  questions QuestionAttempt[]

  @@index([profileId])
  @@index([examId])
  @@index([profileId, examId])
}
// Cascade: ExamAttempt delete → cascade delete QuestionAttempt
```

#### QuestionAttempt
```prisma
model QuestionAttempt {
  id                String    @id @default(uuid())
  attemptId         String
  questionId        String
  selectedOptionId  String?
  textAnswer        String?
  questionSnapshot  Json      // Frozen copy of question + options at attempt time (see Section 8.5)
  isCorrect         Boolean?  // null for WRITING questions not auto-graded in V1
  pointsAwarded     Int       @default(0)
  timeSpentSeconds  Int       @default(0)
  createdAt         DateTime  @default(now())

  attempt  ExamAttempt    @relation(fields: [attemptId], references: [id])
  question Question       @relation(fields: [questionId], references: [id])
  option   QuestionOption? @relation(fields: [selectedOptionId], references: [id])
  mistake  Mistake?

  @@index([attemptId])
  @@index([questionId])
}
// Cascade: QuestionAttempt delete → cascade delete Mistake. Restrict on QuestionOption (preserve history).
```

#### QuestionVersion
```prisma
model QuestionVersion {
  id              String   @id @default(uuid())
  questionId      String
  version         Int
  snapshot        Json     // Full question data at this version
  createdAt       DateTime @default(now())

  question Question @relation(fields: [questionId], references: [id])

  @@unique([questionId, version])
  @@index([questionId])
}
// Cascade: QuestionVersion delete → cascade with Question
```

#### Mistake
```prisma
model Mistake {
  id                String           @id @default(uuid())
  userId            String
  questionAttemptId String           @unique
  category          MistakeCategory
  confidence        Float?
  explanation       String?
  createdAt         DateTime         @default(now())

  profile    Profile         @relation(fields: [userId], references: [id])
  attempt    QuestionAttempt @relation(fields: [questionAttemptId], references: [id])

  @@index([userId])
  @@index([questionAttemptId])
}
// Cascade: Mistake delete → cascade with Profile or QuestionAttempt
```

### 4.3 Import Entities

#### Document
```prisma
model Document {
  id               String          @id @default(uuid())
  filename         String
  mimeType         String
  storagePath      String
  fileSize         Int
  pageCount        Int?
  processingStatus DocumentStatus  @default(PENDING)
  uploadedAt       DateTime        @default(now())

  imports ContentImport[]
  sources ExamSource[]
}
// Cascade: Document delete → cascade delete ContentImport, ExamSource (orphaned files cleaned separately)
```

#### ExamSource
```prisma
model ExamSource {
  id               String   @id @default(uuid())
  examId           String
  documentId       String
  sourceName       String?
  sourceUrl        String?
  originalFilename String
  createdAt        DateTime @default(now())

  exam     Exam     @relation(fields: [examId], references: [id])
  document Document @relation(fields: [documentId], references: [id])

  @@index([examId])
  @@index([documentId])
}
// Cascade: ExamSource delete → cascade with Exam or Document
```

#### ContentImport
```prisma
model ContentImport {
  id               String              @id @default(uuid())
  documentId       String
  examId           String?
  extractionStatus ImportStepStatus    @default(PENDING)
  ocrStatus        ImportStepStatus    @default(N_A)
  aiParsingStatus  ImportStepStatus    @default(PENDING)
  aiConfidence     Float?
  warnings         Json?               // string[]
  errors           Json?               // string[]
  parserVersion    String?
  createdAt        DateTime            @default(now())
  completedAt      DateTime?

  document Document @relation(fields: [documentId], references: [id])
  exam     Exam?    @relation(fields: [examId], references: [id])

  @@index([documentId])
  @@index([examId])
}
// Cascade: ContentImport delete → cascade with Document, Restrict on Exam
```

### 4.4 Enums

```prisma
enum Role {
  STUDENT
  ADMIN
}

enum ExamMode {
  REAL_EXAM
  PRACTICE
  BOTH
}

enum ExamStatus {
  DRAFT
  PUBLISHED
  ARCHIVED
}

enum QuestionType {
  MULTIPLE_CHOICE
  TRUE_FALSE
  SHORT_TEXT
  FILL_BLANK
  MATCHING
  WRITING
}

enum PassageType {
  READING_TEXT
  AUDIO_TRANSCRIPT
  IMAGE
  OTHER
}

enum AttemptStatus {
  IN_PROGRESS
  SUBMITTED
  TIME_UP
}

enum AttemptMode {
  REAL_EXAM
  PRACTICE
}
// Used in ExamAttempt.mode to record which mode was used for each attempt.
// Determines feedback behavior: show explanations in PRACTICE, hide in REAL_EXAM.

enum MistakeCategory {
  CARELESS_MISTAKE
  KNOWLEDGE_GAP
  VOCABULARY_GAP
  GRAMMAR_GAP
  READING_COMPREHENSION
  INFERENCE_ERROR
  QUESTION_MISUNDERSTANDING
  TIME_PRESSURE
  UNKNOWN
}

enum DocumentStatus {
  PENDING
  PROCESSING
  COMPLETED
  FAILED
}

enum ImportStepStatus {
  PENDING
  RUNNING
  COMPLETED
  FAILED
  N_A
}
```

### 4.5 Complete Relationship Diagram

```
Profile ──< ExamAttempt ──< QuestionAttempt ──< Mistake
    │              │
    │              └──> Exam ──< ExamSection ──< Passage ──< Question
    │                                          │               ├──< QuestionOption
    │                                          │               ├──< QuestionAnswer
    │                                          │               ├──< QuestionSkill ──> Skill
    │                                          │               └──< QuestionVersion
    │                                          │
    │                                  ──< ExamSource ──> Document
    │                                  ──< ContentImport ──> Document
    └──> Profile.id references Supabase auth.users.id
```

---

## 5. Question Types

### V1 Supported Types

**MULTIPLE_CHOICE** — Question with 2+ options, one correct answer
- Options stored in `QuestionOption`
- One option has `isCorrect = true`

**TRUE_FALSE** — Question with True/False options
- Stored same as MC with 2 options

**SHORT_TEXT** — Free text answer
- Expected answers in `QuestionAnswer` (multiple acceptable)
- Normalization rules for matching (case, whitespace, accents)

**FILL_BLANK** — One or more blanks
- Blank markers in question text: `___` (each `___` is one blank)
- For N blanks, `QuestionAnswer` contains N records per acceptable answer
- Each `QuestionAnswer.text` stores: `"blank_1: acceptable answer"` format
- Each blank can have multiple acceptable answers (multiple QuestionAnswer records with same blank prefix)
- User submission: `QuestionAttempt.textAnswer` stores JSON array `["answer1", "answer2"]` ordered by blank index

**MATCHING** — Match items from two columns
- Options represent left-side items (column A)
- `QuestionAnswer.text` stores the correct pairing as JSON: `{"A": "1", "B": "3", "C": "2"}`
- User submission stored in `QuestionAttempt.textAnswer` as same format

**WRITING** — Open-ended writing prompt
- No automatic grading in V1
- Stores submission for future AI evaluation
- Points awarded manually or via AI in future

---

## 6. Exam-Taking Interface

### 6.1 Layout

```
┌─────────────────────────────────────────────────────┐
│ [Exam Title]                          [Timer: 42:31] │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Section: Compréhension écrite                       │
│                                                     │
│ Question 7 of 20                                    │
│                                                     │
│ [Passage content shown if question has passage]     │
│                                                     │
│ [Question text]                                     │
│                                                     │
│ ○ A. [option text]                                  │
│ ● B. [option text]                                  │
│ ○ C. [option text]                                  │
│ ○ D. [option text]                                  │
│                                                     │
├─────────────────────────────────────────────────────┤
│ [1] [2] [3] [4] [5] [6] [●7] [8] [9] [10]        │
│ ● = answered  ○ = unanswered  ◆ = marked for review │
│                                                     │
│ [← Previous]           [Mark]           [Next →]    │
└─────────────────────────────────────────────────────┘
```

### 6.2 Requirements

- **Countdown timer** — displays remaining time, auto-submits at zero
- **Autosave** — saves answer state every 10 seconds and on answer change
- **Previous/Next** navigation
- **Question navigator** — grid showing answered/unanswered/marked state
- **Mark for review** — toggle per question
- **Confirm before submission** — modal with summary (answered/unanswered counts)
- **Persist progress** — survives page refresh via localStorage + server sync
- **Connection interruption** — queue saves locally, sync when reconnected
- **Responsive** — works on desktop, tablet, mobile

### 6.3 During Exam

- Do NOT show correct answers
- Do NOT show explanations
- Do NOT allow AI hints
- Only in REAL_EXAM mode

### 6.4 Practice Mode

In PRACTICE mode, additionally allow:
- Immediate feedback after answering
- Reveal correct answer
- Show explanation
- Retry question
- Ask AI about the question

---

## 7. Exam Modes

### REAL_EXAM Mode
- Timer enabled, enforced
- No hints, no explanations, no answer reveal
- Final score only after submission
- Cannot pause and resume across sessions
- `submittedAt` set on manual submission OR time-up auto-submit

### PRACTICE Mode
- Optional timer (user can choose)
- Immediate feedback per question
- Reveal answer and explanation
- Retry question
- Ask AI about the question
- No final score page (per-question feedback instead)

### BOTH Mode
- Exam can be taken in either mode
- User selects mode before starting

---

## 8. Scoring Engine

The scoring engine is deterministic. It never calls an LLM.

### 8.1 Scoring Rules

```typescript
interface ScoringConfig {
  points: number;           // Default 1
  negativePoints: number;   // Default 0
  sectionWeight: number;    // Default 1
}
```

### 8.2 Calculation

`Exam.totalPoints` is nullable and computed at query time as the sum of all `Question.points` in the exam. This prevents desync when questions are added/edited.

```
totalPossible = SUM(question.points) for all questions in exam

For each QuestionAttempt:
  if answer is correct → pointsAwarded = question.points
  if answer is incorrect → pointsAwarded = -question.negativePoints (or 0)
  if unanswered → pointsAwarded = 0

Total Score = sum(pointsAwarded) for all QuestionAttempts
Percentage = (totalScore / totalPossible) * 100
Section Score = sum(pointsAwarded) for questions in section
Section Percentage = (sectionScore / sectionTotalPoints) * 100
```

### 8.3 Answer Correctness

For **MULTIPLE_CHOICE / TRUE_FALSE**:
- Compare `selectedOptionId` to the `QuestionOption` where `isCorrect = true`

For **SHORT_TEXT / FILL_BLANK**:
- Compare `textAnswer` against all `QuestionAnswer` records for the question
- Apply normalization rules (case-insensitive, trim whitespace, etc.)
- If any acceptable answer matches → correct

For **MATCHING**:
- Compare pairing JSON in `textAnswer` against expected pairing

For **WRITING**:
- Not auto-graded in V1
- `isCorrect = null`, `pointsAwarded = 0`

### 8.4 Question Snapshot (Versioning)

When a `QuestionAttempt` is created, a `questionSnapshot` JSON is stored to preserve the exact question state at attempt time. This ensures historical results remain reproducible even if the question is later edited.

```typescript
interface QuestionSnapshot {
  id: string;
  text: string;
  type: QuestionType;
  instructions?: string;
  points: number;
  difficulty?: string;
  options: Array<{
    id: string;
    label: string;
    text: string;
    isCorrect: boolean;
  }>;
  answers: Array<{
    text: string;
    isAcceptable: boolean;
    normalizationRule?: Record<string, boolean>;
  }>;
  skills: Array<{
    name: string;
    category?: string;
  }>;
}
```

When reviewing a historical attempt, the system reads from `questionSnapshot`, NOT from the current Question record. This guarantees:
- Answer options shown match what the user saw
- Correct answer shown matches the version they were tested on
- Points match the version they were tested on

### 8.5 Result Calculation

```typescript
interface ExamResult {
  totalScore: number;
  totalPossible: number;  // computed from SUM(question.points)
  percentage: number;
  timeSpentSeconds: number;
  sectionResults: SectionResult[];
  questionResults: QuestionResult[];
  correctCount: number;
  incorrectCount: number;
  unansweredCount: number;
  accuracy: number;
}

interface SectionResult {
  sectionId: string;
  sectionTitle: string;
  score: number;
  totalPossible: number;
  percentage: number;
}

interface QuestionResult {
  questionId: string;
  questionNumber: number;
  isCorrect: boolean | null;
  pointsAwarded: number;
  selectedOptionId?: string;
  textAnswer?: string;
}
```

---

## 9. Result Page

After submitting an exam:

### Score Summary
```
SCORE
17 / 20

ACCURACY
85%

TIME
58:32
```

### Section Performance
```
SECTION PERFORMANCE

Compréhension écrite    90%  ████████████████░░░░
Grammaire               70%  █████████████░░░░░░░░
Vocabulaire             80%  ███████████████░░░░░░
```

### Question Review
```
QUESTION REVIEW

Q1  ✓  Correct
Q2  ✓  Correct
Q3  ✗  Incorrect — Your answer: B, Correct: C
Q4  ✓  Correct
Q5  —  Unanswered
...
```

Click any question to see:
- Question text
- Their answer
- Correct answer
- Explanation (if available)
- Skills tested
- Mistake classification (if incorrect)

---

## 10. Mistake Engine

### 10.1 Mistake Creation

Every incorrect `QuestionAttempt` creates a `Mistake` record.

### 10.2 Categories

| Category | Description |
|----------|-------------|
| CARELESS_MISTAKE | Knew the answer but made a careless error |
| KNOWLEDGE_GAP | Didn't know the underlying concept |
| VOCABULARY_GAP | Didn't know the required vocabulary |
| GRAMMAR_GAP | Grammar error led to wrong answer |
| READING_COMPREHENSION | Misread or didn't understand the passage |
| INFERENCE_ERROR | Wrong inference from given information |
| QUESTION_MISUNDERSTANDING | Misunderstood what the question asked |
| TIME_PRESSURE | Rushed due to time pressure |
| UNKNOWN | Could not determine the cause |

### 10.3 Classification

In V1, mistake classification is optional and AI-assisted:
- After a wrong answer in practice mode, AI can suggest a category
- AI returns `confidence` (0-1)
- If confidence is low, store as UNKNOWN
- User can override classification
- Do NOT hallucinate the cause

### 10.4 Aggregate Statistics

Mistake statistics are computed from `Mistake` records:
- `mistakeFrequency` per category
- `skillAccuracy` by joining through QuestionSkill
- `recentAccuracy` over last N attempts

---

## 11. Skill System

### 11.1 Taxonomy

Skills are stored in the database as a hierarchical tree. NOT hardcoded.

Example taxonomy:
```
French
├── Compréhension écrite
├── Compréhension orale
├── Production écrite
├── Production orale
├── Grammaire
│   ├── Temps verbaux
│   ├── Subjonctif
│   ├── Conditionnel
│   ├── Pronoms
│   ├── Prépositions
│   └── Accord
├── Vocabulaire
├── Connecteurs logiques
├── Argumentation
└── Inférence
```

### 11.2 Question-Skill Association

Many-to-many via `QuestionSkill`. A question can have 0+ skills.

### 11.3 Skill Accuracy

```
skillAccuracy = correctAttempts / totalAttempts for all questions with that skill
```

Computed on demand, not stored.

---

## 12. Exam Import Module

### 12.1 Supported Formats

- PDF (text-based and scanned)
- JPG, JPEG, PNG

### 12.2 Import Pipeline

**PDF Upload:**
```
Upload PDF
    ↓
Document (stored in Supabase Storage)
    ↓
ContentImport (job created)
    ↓
Step 1: Text Extraction
  ├── pdf-parse extracts selectable text
  └── If no text or low text (< 50 chars/page) → set ocrStatus = RUNNING → Tesseract.js OCR
    ↓
Step 2: AI Parsing
  ├── Send extracted text to AI provider
  ├── AI returns structured JSON (ParsedExam)
  └── Validate with Zod schema
    ↓
Step 3: Review UI
  ├── Show extracted sections, questions, options, answers
  ├── Flag low-confidence extractions
  ├── Allow admin to edit/delete/approve
    ↓
Step 4: Publish
  ├── Create Exam + ExamSection + Question + QuestionOption records
  ├── Link Document → ExamSource
  ├── Set Exam.status = PUBLISHED
```

**Image Upload (JPG/JPEG/PNG):**
```
Upload Image
    ↓
Document (stored in Supabase Storage)
    ↓
ContentImport (job created, ocrStatus = RUNNING)
    ↓
Step 1: OCR (always — images have no text layer)
  └── Tesseract.js processes image → extracted text
    ↓
Step 2-4: Same as PDF (AI Parsing → Review → Publish)
```

### 12.3 AI Parsing Schema

The AI must return structured JSON matching this Zod schema:

```typescript
const ParsedExamSchema = z.object({
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
      type: z.enum(['READING_TEXT', 'AUDIO_TRANSCRIPT', 'IMAGE', 'OTHER']),
    })).optional(),
    questions: z.array(z.object({
      number: z.number(),
      type: z.enum(['MULTIPLE_CHOICE', 'TRUE_FALSE', 'SHORT_TEXT', 'FILL_BLANK', 'MATCHING', 'WRITING']),
      text: z.string(),
      instructions: z.string().optional(),
      passageIndex: z.number().optional(), // index into section.passages
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
```

### 12.4 OCR Handling

```
PDF
  ↓
Check for selectable text (pdf-parse)
  ├── Text found → use extracted text
  └── No text / low text → render pages to images → Tesseract.js OCR
      ↓
  Combine text + layout information
  ↓
  Pass to AI parser
```

OCR confidence is stored in `ContentImport.aiConfidence`.

### 12.5 Retry / Resume

The import pipeline is resumable. Each step has its own status (`extractionStatus`, `ocrStatus`, `aiParsingStatus`). On failure:

1. The failed step's status is set to `FAILED`
2. The `errors` JSON array captures the error message
3. Admin can click "Retry" to re-run only the failed step
4. Completed steps are not re-run
5. On retry, status resets to `RUNNING` and errors are cleared

This allows partial progress to be preserved (e.g., extraction succeeded but AI parsing failed).

### 12.6 Document Review UI

Admin review screen after AI extraction:

```
REVIEW IMPORT

Exam: HSGQG Français 2025
Source: hsgqg_2025_fr.pdf (12 pages)

Section 1: Compréhension écrite
  Q1 ✓  confidence: 0.95
  Q2 ✓  confidence: 0.92
  Q3 ⚠  confidence: 0.61 — answer uncertain
  Q4 ✓  confidence: 0.88

Section 2: Grammaire
  Q5 ✓  confidence: 0.94
  ...

Warnings:
- Q3 answer uncertain — verify against original
- OCR confidence low on page 7

[Edit] [Approve] [Reject]
```

Admin can:
- Edit title, section names, instructions
- Edit question text, options, correct answer
- Delete questions
- Add questions manually
- Reorder questions
- Edit scoring
- Approve or reject entire import

---

## 13. Question Bank

### 13.1 Source

Questions are automatically added to the bank when an imported exam is approved.

### 13.2 Filtering

```
QUESTION BANK

[Search questions...]

Exam:       [All ▼]
Section:    [Grimmaire ▼]
Skill:      [Conditionnel ▼]
Type:       [Multiple Choice ▼]
Difficulty: [B2 ▼]
```

### 13.3 Practice Sessions

Practice sessions reuse the `ExamAttempt` model with `mode = PRACTICE`. No separate PracticeSession model is needed.

**How it works:**
1. User selects filter criteria (skill, difficulty, question count)
2. System queries the QuestionBank for matching questions
3. System creates a temporary "practice exam" (or selects an existing published exam)
4. System creates an `ExamAttempt` with `mode = PRACTICE`
5. User answers questions with immediate feedback
6. Results tracked same as real exams

Users can create practice sessions:
```
Practice

[10] questions
Skill: [Grammar ▼]
Topic: [Subjonctif ▼]
Difficulty: [B2 ▼]

[Start Practice]
```

Or:
```
Practice My Mistakes

[10] questions
Based on your recent mistakes

[Start Practice]
```

### 13.4 AI Explanation

After an incorrect answer in practice mode:

```
[Explain this question]

→ AI receives: question, options, correct answer, user answer, skills
→ Returns:
  1. Why the correct answer is correct
  2. Why the user's answer is incorrect
  3. Relevant French grammar/vocabulary/context
  4. Short takeaway
```

---

## 14. Dashboard

### 14.1 Layout

```
FRENCH EXAM TRAINER

┌─ Recent Exam ──────────────┐  ┌─ Performance ──────────────┐
│ DELF B2 2025               │  │ Overall Accuracy    78%    │
│ Score: 17/20  (85%)        │  │ Exams Taken        12      │
│ 2 hours ago                │  │ Questions Attempted 240    │
└────────────────────────────┘  └────────────────────────────┘

┌─ Weakest Skills ───────────┐  ┌─ Strongest Skills ──────────┐
│ ! Conditionnel      52%   │  │ ✓ Vocabulary          91%   │
│ ! Inference         58%   │  │ ✓ Reading Comprehension 88% │
│ ! Connecteurs       61%   │  │ ✓ Grammaire          85%   │
└────────────────────────────┘  └─────────────────────────────┘

┌─ Recent Mistakes ──────────────────────────────────────────┐
│ Q12 — Conditionnel passé — 3 days ago                      │
│ Q8  — Vocabulaire: "en dépit de" — 5 days ago             │
│ ...                                                        │
└────────────────────────────────────────────────────────────┘

┌─ Available Exams ──────────────────────────────────────────┐
│ DELF B2 2025        [Take Exam] [Practice]                 │
│ HSGQG Français      [Take Exam] [Practice]                 │
│ DALF C1 2024        [Take Exam] [Practice]                 │
└────────────────────────────────────────────────────────────┘
```

### 14.2 Performance Metrics

- Overall accuracy (total correct / total attempted)
- Recent accuracy (last 50 questions)
- Skill accuracy (per skill)
- Mistake frequency (per category)
- Exam history (list of attempts with scores)

---

## 15. Admin Area

Route: `/admin`

### 15.1 Admin Pages

- **Dashboard** — import count, exam count, question count, pending reviews
- **Imports** — list of ContentImport records with status
- **Exams** — list of exams, publish/unpublish
- **Questions** — question bank management
- **Users** — list of profiles (read-only in V1)

### 15.2 Access Control

- Only users with `role = ADMIN` can access `/admin`
- Only admins can publish exams
- Only admins can approve imports
- Students cannot access admin routes

---

## 16. Security

### 16.1 Authentication

- Supabase Auth handles login/register
- Profile created on first login via database trigger or API middleware
- Session managed by Supabase SSR

### 16.2 Authorization

- Middleware checks auth on all `/dashboard/*` and `/admin/*` routes
- API routes verify `profileId` from session
- Users can only access their own `ExamAttempt` records
- Only admins can publish exams and access admin routes

### 16.3 Input Validation

- All API inputs validated with Zod schemas
- File uploads validated: type (PDF/JPG/PNG), size (< 50MB)
- SQL injection prevented by Prisma parameterization
- XSS prevented by React's default escaping

### 16.4 AI Security

- API keys stored in server-side environment variables only
- Never exposed to client bundle
- Rate limiting on AI endpoints (configurable)
- AI output always validated through Zod schemas before use

### 16.5 Supabase Storage Security

- Storage bucket: `exam-documents`
- Allowed MIME types: `application/pdf`, `image/jpeg`, `image/png`
- Max file size: 50MB
- RLS policies:
  - Authenticated users can upload to `exam-documents/{userId}/*`
  - Only the file owner can read their own files
  - Admins can read all files
  - Files are private by default (no public access)

---

## 17. Error Handling

### 17.1 Error States

| Error | Handling |
|-------|----------|
| Invalid PDF | Show "Unsupported file format" with guidance |
| Unreadable scan | Show "Could not read document. Try a clearer image." |
| OCR failure | Show "Text extraction failed. Manual entry available." |
| AI parsing failure | Show "AI extraction failed. Retry or enter manually." |
| Malformed AI JSON | Log error, retry once, then show "Extraction produced invalid data" |
| Missing answer key | Mark answers as `UNKNOWN`, do not hallucinate |
| Duplicate import | Warn "This file may have been imported before" |
| Network failure | Queue action locally, retry when reconnected |
| AI provider failure | Show "AI service temporarily unavailable. Try again later." |
| File too large | Show "File must be under 50MB" |
| Unsupported format | Show "Supported formats: PDF, JPG, JPEG, PNG" |

### 17.2 Principles

- Never crash the application
- Show useful, actionable error states
- Log errors server-side for debugging
- Distinguish user errors from system errors

---

## 18. Testing Strategy

### 18.1 Unit Tests (Vitest)

**Scoring engine:**
- Correct answer → full points
- Incorrect answer → 0 points (or negative)
- Unanswered → 0 points
- Weighted questions
- Section score calculation
- Total percentage calculation

**Exam attempt:**
- Create attempt
- Save answer
- Resume attempt
- Submit attempt
- Time-up auto-submit

**Import parsing:**
- Valid PDF extraction
- Invalid file handling
- AI malformed JSON recovery
- Missing answer key
- Multiple sections
- Multiple question types

**Normalization:**
- Case-insensitive matching
- Whitespace trimming
- Accent normalization

### 18.2 Integration Tests

- API route: create exam attempt
- API route: save question answer
- API route: submit exam
- API route: upload document
- API route: trigger AI parsing

### 18.3 Security Tests

- User cannot access another user's attempt
- Non-admin cannot publish exam
- Unauthenticated user redirected from protected routes

---

## 19. Seed Data

### 19.1 Demo Exam

Create one original demo exam with 3 sections, ~20 questions:

**Demo French Exam — Exercices de Français**

Section 1: Compréhension écrite (5 questions)
- 3 MULTIPLE_CHOICE (reading comprehension)
- 1 TRUE_FALSE
- 1 SHORT_TEXT

Section 2: Grammaire (8 questions)
- 4 MULTIPLE_CHOICE (grammar: temps verbaux, subjonctif, conditionnel, pronoms)
- 2 FILL_BLANK
- 1 MATCHING
- 1 TRUE_FALSE

Section 3: Vocabulaire (7 questions)
- 5 MULTIPLE_CHOICE (vocabulary in context)
- 1 SHORT_TEXT
- 1 FILL_BLANK

All questions are original, not copied from copyrighted exams.

### 19.2 Demo Skills

Seed the skill taxonomy:
```
Compréhension écrite
Grammaire
  ├── Temps verbaux
  ├── Subjonctif
  ├── Conditionnel
  ├── Pronoms
  ├── Prépositions
Vocabulaire
Inférence
```

---

## 20. UX Principles

### Design Language
- Serious, academic, modern, minimal
- Clean typography (system fonts or Inter)
- Minimal color palette (primary blue, success green, error red, warning amber)
- No childish UI, excessive animations, or unnecessary gamification

### Primary Actions
Always visible and obvious:
- Take Exam
- Practice
- Review Mistakes
- Import Exam

### Responsive Breakpoints
- Desktop: 1024px+ (full layout)
- Tablet: 768px-1023px (adjusted grid)
- Mobile: <768px (single column, stacked)

### Loading States
- Skeleton screens for data-heavy pages
- Progress bars for file upload and AI processing
- Spinner for inline actions

### Empty States
- "No exams available yet" with illustration
- "No mistakes to review" with encouragement
- "Import your first exam to get started"

---

## 21. Implementation Phases

### Phase 1 — Core Exam Engine
Database, exam model, sections, questions, question options, exam attempts, question attempts, scoring, exam-taking UI, timer, autosave, result page.

**Deliverable:** User can open exam → answer questions → submit → receive score → review answers.

### Phase 2 — Question Bank & Practice
Question bank, filters, search, practice sessions, mistake tracking, performance statistics.

**Deliverable:** User can browse question bank → practice questions → get feedback → track mistakes.

### Phase 3 — Exam Import
File upload, document storage, PDF text extraction, OCR fallback, AI parser, structured JSON validation, import status, review UI, approve/reject, publish.

**Deliverable:** Admin can upload PDF → AI extracts questions → review → approve → publish as exam.

---

## 22. Future Extensions (Not V1)

These are designed into the architecture but NOT implemented:
- Web exam discovery / crawler
- Adaptive learning
- Personalized study plans
- AI-generated questions
- Spaced repetition
- Writing correction
- Speaking practice
- AI French tutor
- Mock exam generator

---

## 23. Engineering Rules

1. Inspect existing repo patterns before writing code
2. Reuse existing infrastructure (Supabase, Prisma, shadcn)
3. Never hallucinate exam answers
4. Never auto-publish AI-extracted content
5. Never trust raw LLM output without Zod validation
6. Keep scoring deterministic
7. Keep AI provider replaceable
8. Keep exam structure flexible
9. Keep user data isolated
10. Write tests for scoring, attempts, and import
11. Use realistic loading/error/empty states
12. No fake buttons or placeholder workflows
13. Every major feature must work end-to-end
14. Run lint and typecheck after implementation
