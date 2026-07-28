# AI Startup Analyst — Phase 1: Core Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core infrastructure — project setup, AI providers, agent registry, input analyzer, section router, and filesystem storage.

**Architecture:** Next.js App Router with TypeScript. Business logic in `core/` (framework-agnostic). AI providers via abstraction layer (Groq primary, Gemini fallback). Filesystem storage with `ProjectStore` interface for future DB migration.

**Tech Stack:** Next.js 14+, TypeScript 5+, TailwindCSS, shadcn/ui, Zod, Vercel AI SDK, Groq API, Google Gemini API

## Global Constraints

- Node.js 18+ required
- TypeScript strict mode enabled
- No `any` types allowed
- All AI responses validated with Zod schemas
- Filesystem storage in `data/` directory (gitignored)
- Environment variables for API keys: `GROQ_API_KEY`, `GEMINI_API_KEY`
- All timestamps in ISO 8601 format
- All IDs prefixed with `proj_` (projects) or `sec_` (sections)

---

## File Structure

```
ai-startup-analyst/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── core/
│   │   ├── types/
│   │   │   ├── project.ts          # Project, Section, ChatMessage types
│   │   │   ├── agent.ts            # SectionAgentDefinition, AgentState types
│   │   │   └── ai.ts               # GenerateParams, GenerateResult types
│   │   ├── config/
│   │   │   └── index.ts            # Constants (token limits, timeouts)
│   │   ├── agents/
│   │   │   ├── registry.ts         # AgentRegistry class
│   │   │   ├── definitions/
│   │   │   │   ├── executive-summary.ts
│   │   │   │   ├── problem-statement.ts
│   │   │   │   ├── solution.ts
│   │   │   │   ├── target-customers.ts
│   │   │   │   ├── customer-personas.ts
│   │   │   │   ├── tam-sam-som.ts
│   │   │   │   ├── competitor-analysis.ts
│   │   │   │   ├── swot-analysis.ts
│   │   │   │   ├── business-model-canvas.ts
│   │   │   │   ├── revenue-model.ts
│   │   │   │   ├── pricing-strategy.ts
│   │   │   │   ├── go-to-market-strategy.ts
│   │   │   │   ├── mvp-definition.ts
│   │   │   │   ├── feature-prioritization.ts
│   │   │   │   ├── technical-architecture.ts
│   │   │   │   ├── suggested-tech-stack.ts
│   │   │   │   ├── database-design.ts
│   │   │   │   ├── api-overview.ts
│   │   │   │   ├── ui-sitemap.ts
│   │   │   │   ├── product-roadmap.ts
│   │   │   │   ├── risk-analysis.ts
│   │   │   │   ├── financial-assumptions.ts
│   │   │   │   └── launch-checklist.ts
│   │   │   └── index.ts            # Registry singleton + loadAll
│   │   └── services/
│   │       ├── input-analyzer.ts   # Analyzes startup ideas
│   │       └── section-router.ts   # Maps characteristics to sections
│   ├── lib/
│   │   ├── ai/
│   │   │   ├── provider.ts         # AIProvider interface + chain
│   │   │   ├── groq.ts             # Groq provider
│   │   │   ├── gemini.ts           # Gemini provider
│   │   │   └── schemas.ts          # Zod schemas for AI responses
│   │   └── storage/
│   │       ├── interface.ts        # ProjectStore interface
│   │       └── filesystem.ts       # Filesystem implementation
│   └── config/
│       └── env.ts                  # Environment variable validation
├── data/                           # Runtime data (gitignored)
├── tests/
│   ├── core/
│   │   ├── agents/
│   │   │   └── registry.test.ts
│   │   └── services/
│   │       ├── input-analyzer.test.ts
│   │       └── section-router.test.ts
│   └── lib/
│       ├── ai/
│       │   └── provider.test.ts
│       └── storage/
│           └── filesystem.test.ts
├── .env.local                      # API keys (gitignored)
├── .gitignore
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── vitest.config.ts
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `package.json`, `tsconfig.json`, `tailwind.config.ts`, `next.config.js`, `vitest.config.ts`, `.gitignore`, `.env.local`, `src/app/layout.tsx`, `src/app/page.tsx`, `src/app/globals.css`

**Interfaces:** None (foundation only)

- [ ] **Step 1: Initialize Next.js project**

```bash
npx create-next-app@latest ai-startup-analyst --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
cd ai-startup-analyst
```

- [ ] **Step 2: Install dependencies**

```bash
npm install zod pino uuid
npm install -D vitest @vitejs/plugin-react
```

- [ ] **Step 3: Configure vitest**

Create `vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    include: ['tests/**/*.test.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
});
```

- [ ] **Step 4: Configure .gitignore**

Add to `.gitignore`:
```
data/
.env.local
.env
*.log
```

- [ ] **Step 5: Create environment file**

Create `.env.local`:
```
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

- [ ] **Step 6: Run dev server to verify**

```bash
npm run dev
```
Expected: Server starts on http://localhost:3000

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: initialize Next.js project with TypeScript, Tailwind, Vitest"
```

---

## Task 2: Environment Validation

**Files:**
- Create: `src/config/env.ts`

**Interfaces:**
- Produces: `env` object with validated API keys

- [ ] **Step 1: Create env validation**

Create `src/config/env.ts`:
```typescript
import { z } from 'zod';

const envSchema = z.object({
  GROQ_API_KEY: z.string().min(1, 'GROQ_API_KEY is required'),
  GEMINI_API_KEY: z.string().min(1, 'GEMINI_API_KEY is required'),
});

export const env = envSchema.parse(process.env);
```

- [ ] **Step 2: Test env validation fails without keys**

```bash
npx vitest run tests/config/env.test.ts --reporter=verbose
```
Expected: FAIL (file doesn't exist yet)

- [ ] **Step 3: Write env test**

Create `tests/config/env.test.ts`:
```typescript
import { describe, it, expect, vi } from 'vitest';

describe('env validation', () => {
  it('should validate environment variables', async () => {
    vi.stubEnv('GROQ_API_KEY', 'test-key');
    vi.stubEnv('GEMINI_API_KEY', 'test-key');
    
    const { env } = await import('@/config/env');
    expect(env.GROQ_API_KEY).toBe('test-key');
    expect(env.GEMINI_API_KEY).toBe('test-key');
  });
});
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run tests/config/env.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/config/env.ts tests/config/env.test.ts
git commit -m "feat: add environment variable validation with Zod"
```

---

## Task 3: Core Types

**Files:**
- Create: `src/core/types/project.ts`, `src/core/types/agent.ts`, `src/core/types/ai.ts`

**Interfaces:**
- Produces: All TypeScript types used across the system

- [ ] **Step 1: Create project types**

Create `src/core/types/project.ts`:
```typescript
export type SectionId =
  | 'executive-summary'
  | 'problem-statement'
  | 'solution'
  | 'target-customers'
  | 'customer-personas'
  | 'tam-sam-som'
  | 'competitor-analysis'
  | 'swot-analysis'
  | 'business-model-canvas'
  | 'revenue-model'
  | 'pricing-strategy'
  | 'go-to-market-strategy'
  | 'mvp-definition'
  | 'feature-prioritization'
  | 'technical-architecture'
  | 'suggested-tech-stack'
  | 'database-design'
  | 'api-overview'
  | 'ui-sitemap'
  | 'product-roadmap'
  | 'risk-analysis'
  | 'financial-assumptions'
  | 'launch-checklist';

export const ALL_SECTION_IDS: SectionId[] = [
  'executive-summary', 'problem-statement', 'solution',
  'target-customers', 'customer-personas', 'tam-sam-som',
  'competitor-analysis', 'swot-analysis', 'business-model-canvas',
  'revenue-model', 'pricing-strategy', 'go-to-market-strategy',
  'mvp-definition', 'feature-prioritization', 'technical-architecture',
  'suggested-tech-stack', 'database-design', 'api-overview',
  'ui-sitemap', 'product-roadmap', 'risk-analysis',
  'financial-assumptions', 'launch-checklist',
];

export interface InputAnalysisResult {
  originalIdea: string;
  type: 'marketplace' | 'saas' | 'e-commerce' | 'fintech' | 'healthtech'
    | 'edtech' | 'social' | 'hardware' | 'platform' | 'api' | 'agency' | 'other';
  model: 'b2b' | 'b2c' | 'b2b2c' | 'd2c' | 'marketplace' | 'hybrid';
  complexity: 'simple' | 'moderate' | 'complex' | 'highly-complex';
  industry: string;
  hasHardware: boolean;
  hasRegulatoryRequirements: boolean;
  isTwoSidedMarketplace: boolean;
  requiresIntegrations: boolean;
}

export interface Section {
  id: SectionId;
  name: string;
  content: string;
  status: 'pending' | 'generating' | 'complete' | 'failed';
  tokensUsed: { input: number; output: number };
  chatHistory: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tokensUsed?: number;
}

export interface Project {
  id: string;
  idea: string;
  createdAt: string;
  updatedAt: string;
  status: 'analyzing' | 'generating' | 'complete' | 'error';
  analysis: InputAnalysisResult;
  sections: Partial<Record<SectionId, Section>>;
  chatHistory: ChatMessage[];
  metadata: {
    totalTokensUsed: number;
    generationDurationMs: number;
    model: string;
  };
}

export interface ProjectSummary {
  id: string;
  idea: string;
  createdAt: string;
  updatedAt: string;
  sectionCount: number;
  totalTokens: number;
}
```

- [ ] **Step 2: Create agent types**

Create `src/core/types/agent.ts`:
```typescript
import { SectionId, InputAnalysisResult } from './project';

export interface SectionAgentDefinition {
  id: SectionId;
  name: string;
  description: string;
  category: 'strategy' | 'market' | 'financial' | 'technical' | 'operational';
  systemPrompt: string;
  dependencies: SectionId[];
  relevantFor: {
    types?: string[];
    models?: string[];
    flags?: Array<keyof Pick<InputAnalysisResult,
      'hasHardware' | 'hasRegulatoryRequirements' | 'isTwoSidedMarketplace' | 'requiresIntegrations'>>;
  };
  estimatedTokens: { input: number; output: number };
  outputFormat: 'markdown' | 'json' | 'structured-markdown';
  chatEnabled: boolean;
  maxRetries: number;
  timeoutSeconds: number;
}

export interface SectionAgentState {
  definition: SectionAgentDefinition;
  status: 'pending' | 'generating' | 'completed' | 'failed' | 'skipped';
  result?: string;
  error?: string;
  attempts: number;
  startedAt?: Date;
  completedAt?: Date;
  tokensUsed: { input: number; output: number };
}
```

- [ ] **Step 3: Create AI types**

Create `src/core/types/ai.ts`:
```typescript
export interface GenerateParams {
  system: string;
  user: string;
  maxTokens: number;
  temperature?: number;
  timeout?: number;
}

export interface GenerateResult {
  content: string;
  usage: { input: number; output: number };
  model: string;
  finishReason: 'stop' | 'length' | 'timeout' | 'error';
}

export interface AIProvider {
  generate(params: GenerateParams): Promise<GenerateResult>;
}
```

- [ ] **Step 4: Verify types compile**

```bash
npx tsc --noEmit
```
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add src/core/types/
git commit -m "feat: add core TypeScript types for project, agent, and AI"
```

---

## Task 4: Config Constants

**Files:**
- Create: `src/core/config/index.ts`

**Interfaces:**
- Produces: `TOKEN_BUDGETS`, `SECTION_TIMEOUTS`, `APP_CONFIG`

- [ ] **Step 1: Create config**

Create `src/core/config/index.ts`:
```typescript
import { SectionId } from '../types/project';

export const TOKEN_BUDGETS: Record<SectionId, { input: number; output: number }> = {
  'executive-summary':       { input: 1500, output: 800 },
  'problem-statement':       { input: 1200, output: 600 },
  'solution':                { input: 1500, output: 800 },
  'target-customers':        { input: 1200, output: 600 },
  'customer-personas':       { input: 2000, output: 1000 },
  'tam-sam-som':             { input: 2000, output: 1200 },
  'competitor-analysis':     { input: 2500, output: 1500 },
  'swot-analysis':           { input: 2000, output: 1000 },
  'business-model-canvas':   { input: 2500, output: 1500 },
  'revenue-model':           { input: 2500, output: 1200 },
  'pricing-strategy':        { input: 2500, output: 1000 },
  'go-to-market-strategy':   { input: 2500, output: 1500 },
  'mvp-definition':          { input: 2000, output: 1000 },
  'feature-prioritization':  { input: 2500, output: 1200 },
  'technical-architecture':  { input: 3000, output: 2000 },
  'suggested-tech-stack':    { input: 2500, output: 1500 },
  'database-design':         { input: 3000, output: 2000 },
  'api-overview':            { input: 3000, output: 1500 },
  'ui-sitemap':              { input: 2000, output: 1000 },
  'product-roadmap':         { input: 3000, output: 1500 },
  'risk-analysis':           { input: 2500, output: 1200 },
  'financial-assumptions':   { input: 3000, output: 1500 },
  'launch-checklist':        { input: 2500, output: 1200 },
};

export const SECTION_TIMEOUTS: Record<SectionId, number> = {
  'executive-summary': 30,
  'problem-statement': 30,
  'solution': 30,
  'target-customers': 30,
  'customer-personas': 45,
  'tam-sam-som': 45,
  'competitor-analysis': 60,
  'swot-analysis': 45,
  'business-model-canvas': 60,
  'revenue-model': 60,
  'pricing-strategy': 45,
  'go-to-market-strategy': 60,
  'mvp-definition': 45,
  'feature-prioritization': 60,
  'technical-architecture': 90,
  'suggested-tech-stack': 60,
  'database-design': 90,
  'api-overview': 60,
  'ui-sitemap': 45,
  'product-roadmap': 60,
  'risk-analysis': 60,
  'financial-assumptions': 60,
  'launch-checklist': 45,
};

export const APP_CONFIG = {
  MAX_TOKEN_BUDGET: 50000,
  TOKEN_WARNING_PERCENT: 0.8,
  MAX_RETRIES: 2,
  ANALYSIS_CACHE_SIZE: 100,
  DATA_DIR: 'data',
} as const;
```

- [ ] **Step 2: Verify config compiles**

```bash
npx tsc --noEmit
```
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/core/config/
git commit -m "feat: add token budgets and app configuration constants"
```

---

## Task 5: AI Provider Abstraction

**Files:**
- Create: `src/lib/ai/schemas.ts`, `src/lib/ai/groq.ts`, `src/lib/ai/gemini.ts`, `src/lib/ai/provider.ts`
- Test: `tests/lib/ai/provider.test.ts`

**Interfaces:**
- Produces: `AIProviderChain` with `generate()` method

- [ ] **Step 1: Write provider test**

Create `tests/lib/ai/provider.test.ts`:
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AIProviderChain } from '@/lib/ai/provider';

describe('AIProviderChain', () => {
  beforeEach(() => {
    vi.stubEnv('GROQ_API_KEY', 'test-groq-key');
    vi.stubEnv('GEMINI_API_KEY', 'test-gemini-key');
  });

  it('should try providers in order', async () => {
    const mockProvider1 = {
      generate: vi.fn().mockRejectedValue(new Error('Provider 1 failed')),
    };
    const mockProvider2 = {
      generate: vi.fn().mockResolvedValue({
        content: 'Test response',
        usage: { input: 100, output: 50 },
        model: 'test-model',
        finishReason: 'stop',
      }),
    };

    const chain = new AIProviderChain([mockProvider1 as any, mockProvider2 as any]);
    const result = await chain.generate({
      system: 'Test system',
      user: 'Test user',
      maxTokens: 100,
    });

    expect(mockProvider1.generate).toHaveBeenCalledOnce();
    expect(mockProvider2.generate).toHaveBeenCalledOnce();
    expect(result.content).toBe('Test response');
  });

  it('should throw when all providers fail', async () => {
    const mockProvider = {
      generate: vi.fn().mockRejectedValue(new Error('Provider failed')),
    };

    const chain = new AIProviderChain([mockProvider as any]);
    await expect(chain.generate({
      system: 'Test system',
      user: 'Test user',
      maxTokens: 100,
    })).rejects.toThrow('All AI providers failed');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run tests/lib/ai/provider.test.ts --reporter=verbose
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create Zod schemas**

Create `src/lib/ai/schemas.ts`:
```typescript
import { z } from 'zod';

export const generateParamsSchema = z.object({
  system: z.string().min(1),
  user: z.string().min(1),
  maxTokens: z.number().int().positive(),
  temperature: z.number().min(0).max(2).optional(),
  timeout: z.number().int().positive().optional(),
});

export const generateResultSchema = z.object({
  content: z.string(),
  usage: z.object({
    input: z.number().int(),
    output: z.number().int(),
  }),
  model: z.string(),
  finishReason: z.enum(['stop', 'length', 'timeout', 'error']),
});
```

- [ ] **Step 4: Create Groq provider**

Create `src/lib/ai/groq.ts`:
```typescript
import { AIProvider, GenerateParams, GenerateResult } from '@/core/types/ai';
import { env } from '@/config/env';

export class GroqProvider implements AIProvider {
  private model = 'llama-3.1-70b-versatile';

  async generate(params: GenerateParams): Promise<GenerateResult> {
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.GROQ_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: this.model,
        messages: [
          { role: 'system', content: params.system },
          { role: 'user', content: params.user },
        ],
        max_tokens: params.maxTokens,
        temperature: params.temperature ?? 0.7,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Groq API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    const choice = data.choices[0];

    return {
      content: choice.message.content,
      usage: {
        input: data.usage.prompt_tokens,
        output: data.usage.completion_tokens,
      },
      model: data.model,
      finishReason: choice.finish_reason === 'stop' ? 'stop' : 'length',
    };
  }
}
```

- [ ] **Step 5: Create Gemini provider**

Create `src/lib/ai/gemini.ts`:
```typescript
import { AIProvider, GenerateParams, GenerateResult } from '@/core/types/ai';
import { env } from '@/config/env';

export class GeminiProvider implements AIProvider {
  private model = 'gemini-1.5-flash';

  async generate(params: GenerateParams): Promise<GenerateResult> {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${this.model}:generateContent?key=${env.GEMINI_API_KEY}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: `${params.system}\n\n${params.user}` }] }],
        generationConfig: {
          maxOutputTokens: params.maxTokens,
          temperature: params.temperature ?? 0.7,
        },
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Gemini API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    const content = data.candidates[0].content.parts[0].text;

    return {
      content,
      usage: {
        input: data.usageMetadata?.promptTokenCount ?? 0,
        output: data.usageMetadata?.candidatesTokenCount ?? 0,
      },
      model: this.model,
      finishReason: 'stop',
    };
  }
}
```

- [ ] **Step 6: Create provider chain**

Create `src/lib/ai/provider.ts`:
```typescript
import { AIProvider, GenerateParams, GenerateResult } from '@/core/types/ai';
import { GroqProvider } from './groq';
import { GeminiProvider } from './gemini';

export class AIProviderChain implements AIProvider {
  private providers: AIProvider[];

  constructor(providers?: AIProvider[]) {
    this.providers = providers ?? [new GroqProvider(), new GeminiProvider()];
  }

  async generate(params: GenerateParams): Promise<GenerateResult> {
    let lastError: Error | undefined;

    for (const provider of this.providers) {
      try {
        return await provider.generate(params);
      } catch (error) {
        lastError = error as Error;
        console.warn(`Provider ${provider.constructor.name} failed: ${lastError.message}`);
      }
    }

    throw new Error(`All AI providers failed: ${lastError?.message}`);
  }
}

export const aiProvider = new AIProviderChain();
```

- [ ] **Step 7: Run test to verify it passes**

```bash
npx vitest run tests/lib/ai/provider.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/lib/ai/ tests/lib/ai/
git commit -m "feat: add AI provider abstraction with Groq and Gemini"
```

---

## Task 6: Agent Registry

**Files:**
- Create: `src/core/agents/registry.ts`, `src/core/agents/index.ts`
- Test: `tests/core/agents/registry.test.ts`

**Interfaces:**
- Consumes: `SectionAgentDefinition`, `SectionId`
- Produces: `AgentRegistry` class with `register()`, `get()`, `getAll()` methods

- [ ] **Step 1: Write registry test**

Create `tests/core/agents/registry.test.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import { AgentRegistry } from '@/core/agents/registry';
import { SectionAgentDefinition } from '@/core/types/agent';

const mockAgent: SectionAgentDefinition = {
  id: 'executive-summary',
  name: 'Executive Summary',
  description: 'High-level overview',
  category: 'strategy',
  systemPrompt: 'Generate executive summary',
  dependencies: [],
  relevantFor: {},
  estimatedTokens: { input: 1500, output: 800 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 30,
};

describe('AgentRegistry', () => {
  it('should register and retrieve agents', () => {
    const registry = new AgentRegistry();
    registry.register(mockAgent);

    const agent = registry.get('executive-summary');
    expect(agent).toEqual(mockAgent);
  });

  it('should throw for unregistered agent', () => {
    const registry = new AgentRegistry();
    expect(() => registry.get('nonexistent')).toThrow('Agent "nonexistent" not found');
  });

  it('should throw for missing dependencies', () => {
    const registry = new AgentRegistry();
    const agentWithDeps: SectionAgentDefinition = {
      ...mockAgent,
      id: 'revenue-model',
      dependencies: ['business-model-canvas'],
    };

    expect(() => registry.register(agentWithDeps)).toThrow(
      'depends on "business-model-canvas" which is not registered'
    );
  });

  it('should register agents with satisfied dependencies', () => {
    const registry = new AgentRegistry();

    const baseAgent: SectionAgentDefinition = {
      ...mockAgent,
      id: 'business-model-canvas',
      dependencies: [],
    };

    const dependentAgent: SectionAgentDefinition = {
      ...mockAgent,
      id: 'revenue-model',
      dependencies: ['business-model-canvas'],
    };

    registry.register(baseAgent);
    registry.register(dependentAgent);

    expect(registry.get('revenue-model')).toBeDefined();
  });

  it('should return all registered agents', () => {
    const registry = new AgentRegistry();
    registry.register(mockAgent);

    const agent2: SectionAgentDefinition = { ...mockAgent, id: 'problem-statement' };
    registry.register(agent2);

    expect(registry.getAll()).toHaveLength(2);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run tests/core/agents/registry.test.ts --reporter=verbose
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create registry**

Create `src/core/agents/registry.ts`:
```typescript
import { SectionAgentDefinition } from '../types/agent';
import { SectionId } from '../types/project';

export class AgentRegistry {
  private agents: Map<SectionId, SectionAgentDefinition> = new Map();

  register(definition: SectionAgentDefinition): void {
    for (const dep of definition.dependencies) {
      if (!this.agents.has(dep)) {
        throw new Error(
          `Agent "${definition.id}" depends on "${dep}" which is not registered`
        );
      }
    }
    this.agents.set(definition.id, definition);
  }

  get(id: SectionId): SectionAgentDefinition {
    const agent = this.agents.get(id);
    if (!agent) throw new Error(`Agent "${id}" not found in registry`);
    return agent;
  }

  getAll(): SectionAgentDefinition[] {
    return Array.from(this.agents.values());
  }

  getByCategory(category: SectionAgentDefinition['category']): SectionAgentDefinition[] {
    return this.getAll().filter(a => a.category === category);
  }

  has(id: SectionId): boolean {
    return this.agents.has(id);
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run tests/core/agents/registry.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/agents/registry.ts tests/core/agents/
git commit -m "feat: add AgentRegistry with dependency validation"
```

---

## Task 7: Agent Definitions (All 22 Sections)

**Files:**
- Create: `src/core/agents/definitions/*.ts` (22 files), `src/core/agents/index.ts`

**Interfaces:**
- Consumes: `SectionAgentDefinition`
- Produces: Registry singleton with all agents loaded

- [ ] **Step 1: Create executive-summary agent**

Create `src/core/agents/definitions/executive-summary.ts`:
```typescript
import { SectionAgentDefinition } from '../../types/agent';

export const executiveSummaryAgent: SectionAgentDefinition = {
  id: 'executive-summary',
  name: 'Executive Summary',
  description: 'High-level overview of the startup opportunity',
  category: 'strategy',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Executive Summary.

## Startup Idea
{idea}

## Startup Characteristics
{characteristics}

## Output Format
### Executive Summary

#### Vision
[One sentence describing the vision]

#### Problem
[2-3 sentences about the problem being solved]

#### Solution
[2-3 sentences about the proposed solution]

#### Target Market
[2-3 sentences about the target market]

#### Key Differentiators
- [Differentiator 1]
- [Differentiator 2]
- [Differentiator 3]

#### Traction & Milestones
- [Key milestone 1]
- [Key milestone 2]

Be concise but comprehensive. Focus on what matters most to investors and stakeholders.`,

  dependencies: [],
  relevantFor: {},
  estimatedTokens: { input: 1500, output: 800 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 30,
};
```

- [ ] **Step 2: Create remaining 21 agents**

Create each agent file in `src/core/agents/definitions/` following the same pattern. Each agent has:
- Unique system prompt tailored to its section
- Appropriate dependencies (based on dependency graph in spec)
- RelevantFor rules (based on routing rules in spec)
- Token estimates

**Agent Dependencies:**
```
executive-summary: []
problem-statement: []
solution: []
target-customers: []
customer-personas: [target-customers]
tam-sam-som: [target-customers]
competitor-analysis: [target-customers]
swot-analysis: [problem-statement, solution]
business-model-canvas: [solution, target-customers]
revenue-model: [business-model-canvas, target-customers, tam-sam-som]
pricing-strategy: [revenue-model, competitor-analysis]
go-to-market-strategy: [target-customers, competitor-analysis, revenue-model]
mvp-definition: [solution, feature-prioritization]
feature-prioritization: [solution, customer-personas, competitor-analysis]
technical-architecture: [mvp-definition, feature-prioritization]
suggested-tech-stack: [technical-architecture]
database-design: [technical-architecture]
api-overview: [technical-architecture]
ui-sitemap: [mvp-definition]
product-roadmap: [mvp-definition, feature-prioritization, technical-architecture]
risk-analysis: [competitor-analysis, financial-assumptions]
financial-assumptions: [revenue-model, pricing-strategy, business-model-canvas]
launch-checklist: [mvp-definition, technical-architecture]
```

- [ ] **Step 3: Create registry loader**

Create `src/core/agents/index.ts`:
```typescript
import { AgentRegistry } from './registry';
import { executiveSummaryAgent } from './definitions/executive-summary';
import { problemStatementAgent } from './definitions/problem-statement';
import { solutionAgent } from './definitions/solution';
import { targetCustomersAgent } from './definitions/target-customers';
import { customerPersonasAgent } from './definitions/customer-personas';
import { tamSamSomAgent } from './definitions/tam-sam-som';
import { competitorAnalysisAgent } from './definitions/competitor-analysis';
import { swotAnalysisAgent } from './definitions/swot-analysis';
import { businessModelCanvasAgent } from './definitions/business-model-canvas';
import { revenueModelAgent } from './definitions/revenue-model';
import { pricingStrategyAgent } from './definitions/pricing-strategy';
import { goToMarketStrategyAgent } from './definitions/go-to-market-strategy';
import { mvpDefinitionAgent } from './definitions/mvp-definition';
import { featurePrioritizationAgent } from './definitions/feature-prioritization';
import { technicalArchitectureAgent } from './definitions/technical-architecture';
import { suggestedTechStackAgent } from './definitions/suggested-tech-stack';
import { databaseDesignAgent } from './definitions/database-design';
import { apiOverviewAgent } from './definitions/api-overview';
import { uiSitemapAgent } from './definitions/ui-sitemap';
import { productRoadmapAgent } from './definitions/product-roadmap';
import { riskAnalysisAgent } from './definitions/risk-analysis';
import { financialAssumptionsAgent } from './definitions/financial-assumptions';
import { launchChecklistAgent } from './definitions/launch-checklist';

export function createRegistry(): AgentRegistry {
  const registry = new AgentRegistry();

  const agents = [
    executiveSummaryAgent,
    problemStatementAgent,
    solutionAgent,
    targetCustomersAgent,
    customerPersonasAgent,
    tamSamSomAgent,
    competitorAnalysisAgent,
    swotAnalysisAgent,
    businessModelCanvasAgent,
    revenueModelAgent,
    pricingStrategyAgent,
    goToMarketStrategyAgent,
    mvpDefinitionAgent,
    featurePrioritizationAgent,
    technicalArchitectureAgent,
    suggestedTechStackAgent,
    databaseDesignAgent,
    apiOverviewAgent,
    uiSitemapAgent,
    productRoadmapAgent,
    riskAnalysisAgent,
    financialAssumptionsAgent,
    launchChecklistAgent,
  ];

  // Sort by dependency count to catch errors early
  const sorted = [...agents].sort((a, b) => a.dependencies.length - b.dependencies.length);
  for (const agent of sorted) {
    registry.register(agent);
  }

  return registry;
}

export const registry = createRegistry();
```

- [ ] **Step 4: Verify all agents register successfully**

```bash
npx vitest run tests/core/agents/registry.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/agents/definitions/ src/core/agents/index.ts
git commit -m "feat: add all 22 agent definitions with system prompts"
```

---

## Task 8: Filesystem Storage

**Files:**
- Create: `src/lib/storage/interface.ts`, `src/lib/storage/filesystem.ts`
- Test: `tests/lib/storage/filesystem.test.ts`

**Interfaces:**
- Consumes: `Project`, `ProjectSummary`
- Produces: `FilesystemProjectStore` with `save()`, `load()`, `list()`, `delete()` methods

- [ ] **Step 1: Write storage test**

Create `tests/lib/storage/filesystem.test.ts`:
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { FilesystemProjectStore } from '@/lib/storage/filesystem';
import { Project } from '@/core/types/project';
import fs from 'fs/promises';
import path from 'path';

const TEST_DIR = path.join(process.cwd(), 'test-data');

describe('FilesystemProjectStore', () => {
  let store: FilesystemProjectStore;

  beforeEach(async () => {
    await fs.mkdir(TEST_DIR, { recursive: true });
    store = new FilesystemProjectStore(TEST_DIR);
  });

  afterEach(async () => {
    await fs.rm(TEST_DIR, { recursive: true, force: true });
  });

  const mockProject: Project = {
    id: 'proj_test123',
    idea: 'Test startup idea',
    createdAt: '2026-07-26T10:00:00Z',
    updatedAt: '2026-07-26T10:00:00Z',
    status: 'complete',
    analysis: {
      originalIdea: 'Test startup idea',
      type: 'saas',
      model: 'b2b',
      complexity: 'moderate',
      industry: 'test',
      hasHardware: false,
      hasRegulatoryRequirements: false,
      isTwoSidedMarketplace: false,
      requiresIntegrations: false,
    },
    sections: {},
    chatHistory: [],
    metadata: {
      totalTokensUsed: 1000,
      generationDurationMs: 5000,
      model: 'llama-3.1-70b-versatile',
    },
  };

  it('should save and load a project', async () => {
    await store.save(mockProject);
    const loaded = await store.load('proj_test123');

    expect(loaded).toEqual(mockProject);
  });

  it('should return null for non-existent project', async () => {
    const loaded = await store.load('proj_nonexistent');
    expect(loaded).toBeNull();
  });

  it('should list all projects', async () => {
    await store.save(mockProject);
    await store.save({ ...mockProject, id: 'proj_test456', idea: 'Another idea' });

    const list = await store.list();
    expect(list).toHaveLength(2);
  });

  it('should delete a project', async () => {
    await store.save(mockProject);
    await store.delete('proj_test123');

    const loaded = await store.load('proj_test123');
    expect(loaded).toBeNull();
  });

  it('should handle concurrent saves', async () => {
    const promises = Array.from({ length: 5 }, (_, i) =>
      store.save({ ...mockProject, id: `proj_${i}` })
    );

    await Promise.all(promises);
    const list = await store.list();
    expect(list).toHaveLength(5);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run tests/lib/storage/filesystem.test.ts --reporter=verbose
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create storage interface**

Create `src/lib/storage/interface.ts`:
```typescript
import { Project, ProjectSummary } from '@/core/types/project';

export interface ProjectStore {
  save(project: Project): Promise<void>;
  load(id: string): Promise<Project | null>;
  list(): Promise<ProjectSummary[]>;
  delete(id: string): Promise<void>;
}
```

- [ ] **Step 4: Create filesystem implementation**

Create `src/lib/storage/filesystem.ts`:
```typescript
import { Project, ProjectSummary } from '@/core/types/project';
import { ProjectStore } from './interface';
import fs from 'fs/promises';
import path from 'path';

export class FilesystemProjectStore implements ProjectStore {
  private baseDir: string;

  constructor(baseDir: string) {
    this.baseDir = baseDir;
  }

  async save(project: Project): Promise<void> {
    const dir = path.join(this.baseDir, project.id);
    await fs.mkdir(dir, { recursive: true });

    // Atomic write: write to temp, then rename
    const tmpPath = path.join(dir, 'project.json.tmp');
    const finalPath = path.join(dir, 'project.json');
    await fs.writeFile(tmpPath, JSON.stringify(project, null, 2));
    await fs.rename(tmpPath, finalPath);
  }

  async load(id: string): Promise<Project | null> {
    try {
      const filePath = path.join(this.baseDir, id, 'project.json');
      const data = await fs.readFile(filePath, 'utf-8');
      return JSON.parse(data);
    } catch {
      return null;
    }
  }

  async list(): Promise<ProjectSummary[]> {
    try {
      const entries = await fs.readdir(this.baseDir);
      const summaries: ProjectSummary[] = [];

      for (const entry of entries) {
        const project = await this.load(entry);
        if (project) {
          summaries.push({
            id: project.id,
            idea: project.idea,
            createdAt: project.createdAt,
            updatedAt: project.updatedAt,
            sectionCount: Object.keys(project.sections).length,
            totalTokens: project.metadata.totalTokensUsed,
          });
        }
      }

      return summaries;
    } catch {
      return [];
    }
  }

  async delete(id: string): Promise<void> {
    const dir = path.join(this.baseDir, id);
    await fs.rm(dir, { recursive: true, force: true });
  }
}
```

- [ ] **Step 5: Run test to verify it passes**

```bash
npx vitest run tests/lib/storage/filesystem.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/lib/storage/ tests/lib/storage/
git commit -m "feat: add filesystem project storage with atomic writes"
```

---

## Task 9: Section Router

**Files:**
- Create: `src/core/services/section-router.ts`
- Test: `tests/core/services/section-router.test.ts`

**Interfaces:**
- Consumes: `InputAnalysisResult`, `AgentRegistry`
- Produces: `SectionRouter` with `resolve()` method returning `SectionId[]`

- [ ] **Step 1: Write router test**

Create `tests/core/services/section-router.test.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import { SectionRouter } from '@/core/services/section-router';
import { createRegistry } from '@/core/agents';
import { InputAnalysisResult } from '@/core/types/project';

describe('SectionRouter', () => {
  const registry = createRegistry();
  const router = new SectionRouter(registry);

  const baseAnalysis: InputAnalysisResult = {
    originalIdea: 'Test idea',
    type: 'saas',
    model: 'b2b',
    complexity: 'moderate',
    industry: 'test',
    hasHardware: false,
    hasRegulatoryRequirements: false,
    isTwoSidedMarketplace: false,
    requiresIntegrations: false,
  };

  it('should include always-relevant sections', () => {
    const sections = router.resolve(baseAnalysis);
    expect(sections).toContain('executive-summary');
    expect(sections).toContain('problem-statement');
    expect(sections).toContain('solution');
    expect(sections).toContain('launch-checklist');
  });

  it('should exclude agency-specific sections for non-agency', () => {
    const sections = router.resolve(baseAnalysis);
    expect(sections).toContain('tam-sam-som');
    expect(sections).toContain('revenue-model');
  });

  it('should exclude TAM/SAM/SOM for agency type', () => {
    const agencyAnalysis = { ...baseAnalysis, type: 'agency' as const };
    const sections = router.resolve(agencyAnalysis);
    expect(sections).not.toContain('tam-sam-som');
    expect(sections).not.toContain('revenue-model');
  });

  it('should include technical architecture for complex projects', () => {
    const complexAnalysis = { ...baseAnalysis, complexity: 'complex' as const };
    const sections = router.resolve(complexAnalysis);
    expect(sections).toContain('technical-architecture');
  });

  it('should exclude technical architecture for simple projects', () => {
    const simpleAnalysis = { ...baseAnalysis, complexity: 'simple' as const };
    const sections = router.resolve(simpleAnalysis);
    expect(sections).not.toContain('technical-architecture');
  });

  it('should include API overview for SaaS type', () => {
    const sections = router.resolve(baseAnalysis);
    expect(sections).toContain('api-overview');
  });

  it('should exclude API overview for agency type', () => {
    const agencyAnalysis = { ...baseAnalysis, type: 'agency' as const };
    const sections = router.resolve(agencyAnalysis);
    expect(sections).not.toContain('api-overview');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run tests/core/services/section-router.test.ts --reporter=verbose
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create section router**

Create `src/core/services/section-router.ts`:
```typescript
import { AgentRegistry } from '../agents/registry';
import { InputAnalysisResult, SectionId } from '../types/project';

export class SectionRouter {
  constructor(private registry: AgentRegistry) {}

  resolve(analysis: InputAnalysisResult): SectionId[] {
    const allAgents = this.registry.getAll();
    const relevant: SectionId[] = [];

    for (const agent of allAgents) {
      if (this.isRelevant(agent, analysis)) {
        relevant.push(agent.id);
      }
    }

    return relevant;
  }

  private isRelevant(agent: { relevantFor: Record<string, any> }, analysis: InputAnalysisResult): boolean {
    const { relevantFor } = agent;

    // Empty relevantFor = always relevant
    if (!relevantFor.types?.length && !relevantFor.models?.length && !relevantFor.flags?.length) {
      return true;
    }

    let match = false;

    if (relevantFor.types?.length) {
      match = match || relevantFor.types.includes(analysis.type);
    }
    if (relevantFor.models?.length) {
      match = match || relevantFor.models.includes(analysis.model);
    }
    if (relevantFor.flags?.length) {
      match = match || relevantFor.flags.some((flag: string) => analysis[flag as keyof InputAnalysisResult]);
    }

    return match;
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run tests/core/services/section-router.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/services/section-router.ts tests/core/services/
git commit -m "feat: add SectionRouter with deterministic section filtering"
```

---

## Task 10: Input Analyzer

**Files:**
- Create: `src/core/services/input-analyzer.ts`
- Test: `tests/core/services/input-analyzer.test.ts`

**Interfaces:**
- Consumes: `AIProvider`
- Produces: `InputAnalyzerService` with `analyze()` method

- [ ] **Step 1: Write input analyzer test**

Create `tests/core/services/input-analyzer.test.ts`:
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { InputAnalyzerService } from '@/core/services/input-analyzer';

describe('InputAnalyzerService', () => {
  let analyzer: InputAnalyzerService;
  let mockProvider: any;

  beforeEach(() => {
    mockProvider = {
      generate: vi.fn().mockResolvedValue({
        content: JSON.stringify({
          type: 'marketplace',
          model: 'b2c',
          complexity: 'complex',
          industry: 'pet-care',
          hasHardware: false,
          hasRegulatoryRequirements: false,
          isTwoSidedMarketplace: true,
          requiresIntegrations: true,
        }),
        usage: { input: 100, output: 50 },
        model: 'test-model',
        finishReason: 'stop',
      }),
    };

    analyzer = new InputAnalyzerService(mockProvider);
  });

  it('should analyze a startup idea', async () => {
    const result = await analyzer.analyze('I want to build Airbnb for pets');

    expect(result.originalIdea).toBe('I want to build Airbnb for pets');
    expect(result.type).toBe('marketplace');
    expect(result.model).toBe('b2c');
    expect(result.isTwoSidedMarketplace).toBe(true);
  });

  it('should call AI provider with correct params', async () => {
    await analyzer.analyze('Test idea');

    expect(mockProvider.generate).toHaveBeenCalledWith(
      expect.objectContaining({
        maxTokens: 500,
        temperature: 0.1,
      })
    );
  });

  it('should handle invalid JSON response', async () => {
    mockProvider.generate.mockResolvedValue({
      content: 'Invalid JSON',
      usage: { input: 100, output: 50 },
      model: 'test-model',
      finishReason: 'stop',
    });

    await expect(analyzer.analyze('Test idea')).rejects.toThrow();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run tests/core/services/input-analyzer.test.ts --reporter=verbose
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create input analyzer**

Create `src/core/services/input-analyzer.ts`:
```typescript
import { AIProvider } from '@/core/types/ai';
import { InputAnalysisResult } from '@/core/types/project';

export class InputAnalyzerService {
  private systemPrompt = `Analyze this startup idea and output JSON with:
- type: marketplace|saas|e-commerce|fintech|healthtech|edtech|social|hardware|platform|api|agency|other
- model: b2b|b2c|b2b2c|d2c|marketplace|hybrid
- complexity: simple|moderate|complex|highly-complex
- industry: specific industry string (e.g., "pet-care", "fintech", "healthcare")
- hasHardware: boolean — does this involve physical hardware?
- hasRegulatoryRequirements: boolean — is this a regulated industry?
- isTwoSidedMarketplace: boolean — are there two distinct user groups?
- requiresIntegrations: boolean — does this need third-party APIs/services?
Output ONLY valid JSON. No explanation.`;

  constructor(private aiProvider: AIProvider) {}

  async analyze(idea: string): Promise<InputAnalysisResult> {
    const response = await this.aiProvider.generate({
      system: this.systemPrompt,
      user: idea,
      maxTokens: 500,
      temperature: 0.1,
    });

    return {
      originalIdea: idea,
      ...JSON.parse(response.content),
    };
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run tests/core/services/input-analyzer.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/services/input-analyzer.ts tests/core/services/
git commit -m "feat: add InputAnalyzerService for startup idea analysis"
```

---

## Task 11: Run All Tests

- [ ] **Step 1: Run full test suite**

```bash
npx vitest run --reporter=verbose
```
Expected: All tests pass

- [ ] **Step 2: Check for TypeScript errors**

```bash
npx tsc --noEmit
```
Expected: No errors

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete Phase 1 core foundation"
```

---

## Phase 1 Summary

After completing all tasks, you will have:

- ✅ Next.js project with TypeScript, Tailwind, Vitest
- ✅ Environment validation with Zod
- ✅ Core types (Project, Section, Agent, AI)
- ✅ AI provider abstraction (Groq + Gemini fallback)
- ✅ Agent registry with dependency validation
- ✅ 22 agent definitions with system prompts
- ✅ Filesystem storage with atomic writes
- ✅ Section router with deterministic filtering
- ✅ Input analyzer for startup ideas

**Next Phase:** Phase 2 will add the orchestrator, generation pipeline, and workspace UI.
