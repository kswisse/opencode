# AI Startup Analyst — Complete System Design

**Date:** 2026-07-26
**Status:** Draft — awaiting review
**Scope:** AI-powered startup analysis platform

---

## 1. Product Overview

### What It Does

User enters a startup idea → system intelligently analyzes it → determines which analysis sections are relevant → generates only those sections → presents as a workspace → allows chat-based refinement per section.

**Example:**
- Input: "I want to build Airbnb for pets"
- System identifies: marketplace, two-sided, B2C, pet-care industry
- Generates relevant sections: TAM/SAM/SOM for pet market, competitor analysis, marketplace business model, trust & safety considerations
- User can chat to refine any section

### Key Design Principles

1. **Token-efficient**: Only generate relevant sections, not all 22
2. **Intelligent routing**: AI analyzes input → maps to relevant sections
3. **Independent modules**: Each section is a replaceable agent
4. **Free first**: Use free AI providers (Groq, Gemini) for Phase 1
5. **Extensible**: Designed for future multi-agent orchestration

---

## 2. Tech Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Framework | Next.js 14+ (App Router) | API routes + UI in one framework |
| Language | TypeScript 5+ | Type safety for complex data models |
| AI SDK | Vercel AI SDK | Provider-agnostic, streaming support |
| Validation | Zod | Runtime validation for AI responses |
| Styling | TailwindCSS + shadcn/ui | Modern UI, dark mode, components |
| State | Zustand | Lightweight client state |
| Server State | TanStack Query | API caching, optimistic updates |
| Animation | Framer Motion | Smooth transitions |
| Logging | Pino | Structured logging |

---

## 3. Folder Structure

```
src/
├── app/                          # Next.js App Router
│   ├── page.tsx                  # Landing page
│   ├── project/
│   │   ├── new.tsx               # Create new project
│   │   └── [id]/
│   │       ├── page.tsx          # Workspace view
│   │       └── section/
│   │           └── [sectionId]/  # Section detail + chat
│   └── api/
│       ├── projects/
│       │   ├── route.ts          # POST /api/projects
│       │   └── [id]/
│       │       ├── route.ts      # GET /api/projects/:id
│       │       ├── generate/route.ts
│       │       └── sections/
│       │           └── [sectionId]/
│       │               ├── route.ts
│       │               ├── regenerate/route.ts
│       │               └── chat/route.ts
│       └── export/
│           └── [id]/route.ts
│
├── core/                         # Business logic
│   ├── agents/
│   │   ├── registry.ts
│   │   ├── orchestrator.ts
│   │   ├── context-builder.ts
│   │   ├── token-manager.ts
│   │   ├── dependency-graph.ts
│   │   └── definitions/          # 22 agent files
│   ├── services/
│   │   ├── input-analyzer.ts
│   │   ├── section-router.ts
│   │   ├── generation-service.ts
│   │   ├── project-service.ts
│   │   ├── chat-service.ts
│   │   └── export-service.ts
│   ├── types/
│   │   ├── project.ts
│   │   ├── agent.ts
│   │   └── ai.ts
│   └── config/
│       └── index.ts
│
├── lib/                          # Utilities
│   ├── ai/
│   │   ├── provider.ts           # Provider abstraction
│   │   ├── prompts/
│   │   │   ├── input-analyzer.md
│   │   │   └── sections/
│   │   └── parsers.ts
│   ├── storage/
│   │   ├── filesystem.ts
│   │   └── interface.ts
│   └── utils/
│       ├── id.ts
│       └── markdown.ts
│
├── components/
│   ├── workspace/
│   │   ├── WorkspaceView.tsx
│   │   ├── SectionCard.tsx
│   │   └── SectionDetail.tsx
│   ├── chat/
│   │   ├── ChatPanel.tsx
│   │   └── MessageBubble.tsx
│   └── ui/                       # shadcn/ui
│
└── config/
    └── constants.ts
```

---

## 4. Core Data Models

### TypeScript Interfaces

```typescript
// core/types/project.ts

type SectionId =
  | "executive-summary"
  | "problem-statement"
  | "solution"
  | "target-customers"
  | "customer-personas"
  | "tam-sam-som"
  | "competitor-analysis"
  | "swot-analysis"
  | "business-model-canvas"
  | "revenue-model"
  | "pricing-strategy"
  | "go-to-market-strategy"
  | "mvp-definition"
  | "feature-prioritization"
  | "technical-architecture"
  | "suggested-tech-stack"
  | "database-design"
  | "api-overview"
  | "ui-sitemap"
  | "product-roadmap"
  | "risk-analysis"
  | "financial-assumptions"
  | "launch-checklist";

interface Project {
  id: string;
  idea: string;
  createdAt: string;
  updatedAt: string;
  status: "analyzing" | "generating" | "complete" | "error";
  analysis: InputAnalysisResult;
  sections: Record<SectionId, Section>;
  chatHistory: ChatMessage[];
  metadata: {
    totalTokensUsed: number;
    generationDurationMs: number;
    model: string;
  };
}

interface Section {
  id: SectionId;
  name: string;
  content: string;
  status: "pending" | "generating" | "complete" | "failed";
  tokensUsed: { input: number; output: number };
  chatHistory: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  tokensUsed?: number;
}

interface InputAnalysisResult {
  originalIdea: string;
  type: "marketplace" | "saas" | "e-commerce" | "fintech" | "healthtech"
    | "edtech" | "social" | "hardware" | "platform" | "api" | "agency" | "other";
  model: "b2b" | "b2c" | "b2b2c" | "d2c" | "marketplace" | "hybrid";
  complexity: "simple" | "moderate" | "complex" | "highly-complex";
  industry: string;
  hasHardware: boolean;
  hasRegulatoryRequirements: boolean;
  isTwoSidedMarketplace: boolean;
  requiresIntegrations: boolean;
}
```

---

## 5. System Architecture

### Data Flow

```
User Input → InputAnalyzer → SectionRouter → GenerationService → ProjectService
                  (1 LLM)      (0 LLM)        (N LLM)            (filesystem)
                                                                      ↓
                                                              Workspace Output
```

### Service Definitions

```typescript
// core/services/generation-service.ts

class GenerationService {
  constructor(
    private inputAnalyzer: InputAnalyzerService,
    private sectionRouter: SectionRouterService,
    private orchestrator: Orchestrator,
    private projectService: ProjectService,
    private tokenManager: TokenManager,
  ) {}

  async generate(idea: string): Promise<Project> {
    // Step 1: Analyze input (1 LLM call, ~500 tokens)
    const analysis = await this.inputAnalyzer.analyze(idea);

    // Step 2: Route to relevant sections (0 LLM calls, deterministic)
    const sections = this.sectionRouter.resolve(analysis);

    // Step 3: Check token budget
    const estimatedTokens = this.tokenManager.estimateForSections(sections);
    if (estimatedTokens > BUDGET_LIMIT) {
      throw new Error(`Estimated ${estimatedTokens} tokens exceeds limit`);
    }

    // Step 4: Create project
    const project = await this.projectService.create(idea, analysis);

    // Step 5: Generate sections (N LLM calls)
    await this.orchestrator.generate(project, sections);

    return project;
  }
}
```

```typescript
// core/services/input-analyzer.ts

class InputAnalyzerService {
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

---

## 6. AI Integration (Free Providers)

### Provider Chain with Fallback

```typescript
// lib/ai/provider.ts

interface AIProvider {
  generate(params: GenerateParams): Promise<GenerateResult>;
  stream(params: GenerateParams): AsyncGenerator<Chunk>;
}

// Primary: Groq (free, fast, 30 req/min)
class GroqProvider implements AIProvider {
  private model = "llama-3.1-70b-versatile";

  async generate(params: GenerateParams): Promise<GenerateResult> {
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.GROQ_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: this.model,
        messages: [
          { role: "system", content: params.system },
          { role: "user", content: params.user },
        ],
        max_tokens: params.maxTokens,
        temperature: params.temperature ?? 0.7,
      }),
    });

    if (!response.ok) throw new Error(`Groq API error: ${response.status}`);
    return response.json();
  }
}

// Fallback: Google Gemini Flash (free tier)
class GeminiProvider implements AIProvider { ... }

// Provider chain
class AIProviderChain implements AIProvider {
  private providers = [
    new GroqProvider(),
    new GeminiProvider(),
  ];

  async generate(params: GenerateParams): Promise<GenerateResult> {
    for (const provider of this.providers) {
      try {
        return await provider.generate(params);
      } catch (error) {
        console.warn(`Provider failed, trying next: ${error.message}`);
      }
    }
    throw new Error("All AI providers failed");
  }
}
```

### Token Budget

| Component | Tokens | Notes |
|-----------|--------|-------|
| InputAnalyzer | ~500 | One-time |
| Per Section | 2000-5000 | Varies |
| Context Overhead | +15% | Workspace context |
| **Total (typical)** | **15,000-30,000** | ~10-15 sections |

### Token Costs (Free Tiers)

| Provider | Free Limit | Cost |
|----------|------------|------|
| Groq | 30 req/min | $0 |
| Gemini Flash | 15 RPM, 1M tokens/day | $0 |
| **Total per analysis** | **~$0** | **Free** |

---

## 7. Agent System

### Agent Registry

```typescript
// core/agents/registry.ts

interface SectionAgentDefinition {
  id: SectionId;
  name: string;
  description: string;
  category: "strategy" | "market" | "financial" | "technical" | "operational";
  systemPrompt: string;
  dependencies: SectionId[];
  relevantFor: {
    types?: string[];
    models?: string[];
    flags?: string[];
  };
  estimatedTokens: { input: number; output: number };
  outputFormat: "markdown" | "json" | "structured-markdown";
  chatEnabled: boolean;
  maxRetries: number;
  timeoutSeconds: number;
}

class AgentRegistry {
  private agents: Map<SectionId, SectionAgentDefinition> = new Map();

  register(definition: SectionAgentDefinition): void {
    for (const dep of definition.dependencies) {
      if (!this.agents.has(dep)) {
        throw new Error(`Agent "${definition.id}" depends on "${dep}" which is not registered`);
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
}
```

### Example Agent Definition

```typescript
// core/agents/definitions/revenue-model.ts

export const revenueModelAgent: SectionAgentDefinition = {
  id: "revenue-model",
  name: "Revenue Model",
  description: "How the startup makes money — revenue streams, unit economics, growth levers",
  category: "financial",

  systemPrompt: `You are a senior startup analyst specializing in revenue models.

Generate a comprehensive Revenue Model section for a startup analysis.

## Startup Idea
{idea}

## Startup Characteristics
{characteristics}

## Dependencies (use as context, don't repeat)
{dependencies}

## Output Format
Produce a structured markdown section with:

### Revenue Streams
- Primary: [main revenue mechanism]
- Secondary: [additional streams]
- Potential: [future revenue opportunities]

### Unit Economics
- CAC (Customer Acquisition Cost): estimate
- LTV (Lifetime Value): estimate
- LTV/CAC ratio and target
- Payback period

### Revenue Drivers
- [What factors most impact revenue]
- [Growth levers specific to this model]

### Key Assumptions
- [Critical assumptions underlying revenue projections]
- [Scalability considerations]

Be specific to THIS startup. Reference the characteristics and dependencies above.
Use ranges when exact numbers are speculative. Always explain your reasoning.`,

  dependencies: ["business-model-canvas", "target-customers", "tam-sam-som"],

  relevantFor: {
    // All startups need revenue modeling
  },

  estimatedTokens: { input: 2500, output: 1500 },
  outputFormat: "markdown",
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
```

### Routing Rules

| Section | Relevant When |
|---------|---------------|
| Executive Summary | Always |
| Problem Statement | Always |
| Solution | Always |
| Target Customers | Always |
| Customer Personas | Always |
| TAM/SAM/SOM | Not "agency" type |
| Competitor Analysis | Not "agency" type |
| SWOT Analysis | Always |
| Business Model Canvas | Always |
| Revenue Model | Not "agency" type |
| Pricing Strategy | Not "agency" type |
| Go-to-Market Strategy | Always |
| MVP Definition | Not "agency" type |
| Feature Prioritization | Not "agency" type |
| Technical Architecture | complexity != "simple" |
| Suggested Tech Stack | Not "agency" type |
| Database Design | complexity in ["complex", "highly-complex"] |
| API Overview | type in ["saas", "platform", "api", "marketplace"] |
| UI Sitemap | type != "api" AND type != "agency" |
| Product Roadmap | Always |
| Risk Analysis | complexity != "simple" |
| Financial Assumptions | Not "agency" type |
| Launch Checklist | Always |

---

## 8. Storage

### Filesystem Structure

```
data/
├── projects/
│   ├── {project-id}/
│   │   ├── project.json
│   │   └── sections/
│   │       ├── executive-summary.json
│   │       ├── problem-statement.json
│   │       └── ...
│   └── {project-id-2}/
│       └── ...
└── cache/
    └── analysis-cache.json
```

### Storage Interface

```typescript
// core/storage/interface.ts

interface ProjectStore {
  save(project: Project): Promise<void>;
  load(id: string): Promise<Project | null>;
  list(): Promise<ProjectSummary[]>;
  delete(id: string): Promise<void>;
}

// core/storage/filesystem.ts

class FilesystemProjectStore implements ProjectStore {
  constructor(private baseDir: string) {}

  async save(project: Project): Promise<void> {
    const dir = path.join(this.baseDir, project.id);
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(
      path.join(dir, "project.json"),
      JSON.stringify(project, null, 2)
    );
  }

  async load(id: string): Promise<Project | null> {
    try {
      const data = await fs.readFile(
        path.join(this.baseDir, id, "project.json"),
        "utf-8"
      );
      return JSON.parse(data);
    } catch {
      return null;
    }
  }
}
```

---

## 9. API Contracts

```
POST   /api/projects                    Create new project
GET    /api/projects/:id                Get project workspace
DELETE /api/projects/:id                Delete project
POST   /api/projects/:id/generate       Start generation (SSE)
POST   /api/projects/:id/sections/:sid/chat      Chat refinement (SSE)
POST   /api/projects/:id/sections/:sid/regenerate Regenerate section
POST   /api/projects/:id/export         Export Markdown/PDF
GET    /api/projects                     List all projects
```

### SSE Events

```typescript
// Generation events
type GenerationEvent =
  | { type: "analysis-complete"; data: InputAnalysisResult }
  | { type: "section-started"; sectionId: SectionId }
  | { type: "section-token"; sectionId: SectionId; delta: string }
  | { type: "section-complete"; sectionId: SectionId; content: string }
  | { type: "section-failed"; sectionId: SectionId; error: string }
  | { type: "generation-complete"; totalTokens: number; duration: number }
  | { type: "error"; message: string };

// Chat events
type ChatEvent =
  | { type: "message-start"; }
  | { type: "message-delta"; delta: string }
  | { type: "message-complete"; message: ChatMessage }
  | { type: "error"; message: string };
```

---

## 10. Milestones

### Phase 1: Core Foundation (2 weeks)
- [ ] Project setup (Next.js, TypeScript, Tailwind, shadcn/ui)
- [ ] AI Provider abstraction (Groq + Gemini)
- [ ] InputAnalyzer + SectionRouter
- [ ] Agent Registry + 22 agent definitions
- [ ] Filesystem storage
- [ ] Basic API routes
- [ ] Input UI (homepage)

### Phase 2: Generation Pipeline (2 weeks)
- [ ] Orchestrator (sequential execution)
- [ ] Context Builder
- [ ] Token Manager
- [ ] Generation API with SSE streaming
- [ ] Workspace UI (view all sections)
- [ ] Section detail view

### Phase 3: Chat Refinement (1 week)
- [ ] Chat API per section
- [ ] Chat UI with streaming
- [ ] Update section after refinement

### Phase 4: Export & Polish (1 week)
- [ ] Export to Markdown
- [ ] Export to PDF
- [ ] Loading states, animations
- [ ] Error handling
- [ ] Project list page

**Total: ~6 weeks for MVP**

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Free tier rate limits | Generation delays | Multi-provider fallback, queue system |
| AI output quality | Poor analysis | Carefully crafted prompts, human review |
| Token budget overrun | Unexpected costs | Hard limits, warnings at 80% |
| Filesystem scalability | Slow with many projects | Migrate to DB later |
| Circular dependencies | Generation fails | Pre-validated dependency graph |

---

## 12. Future Enhancements

- **Phase 2**: Parallel generation, provider-per-section optimization
- **Phase 3**: Full multi-agent with inter-agent communication
- **Phase 4**: User accounts, subscription, database storage
- **Phase 5**: Marketplace, API access, integrations
