# AI Startup Analyst — Multi-Agent Orchestration Design

**Date:** 2026-07-26
**Status:** Draft — awaiting review
**Scope:** Multi-agent orchestration architecture for an AI-powered startup analysis platform

---

## 1. System Overview

User enters a startup idea → system analyzes it → determines which of 22 sections are relevant → generates only those sections → presents as a workspace → allows chat-based refinement per section.

### High-Level Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  User Input  │────▶│ InputAnalyzer │────▶│  SectionRouter   │────▶│  AgentPool   │
│ "Airbnb for  │     │  (LLM call)   │     │  (deterministic) │     │ (LLM calls)  │
│   pets"      │     │               │     │                  │     │              │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────┬───────┘
                                                                         │
                                                                         ▼
                                                                ┌──────────────┐
                                                                │  Workspace   │
                                                                │  (assembled  │
                                                                │   sections)  │
                                                                └──────┬───────┘
                                                                         │
                                                                         ▼
                                                                ┌──────────────┐
                                                                │ Section Chat │
                                                                │ (refinement) │
                                                                └──────────────┘
```

---

## 2. Agent Architecture Pattern

### 2.1 Agent Definition

Each section agent is defined as a **lightweight configuration object**, not a heavy class. The agent definition specifies what the LLM needs to produce that section, and the orchestrator handles execution, context injection, and result assembly.

```typescript
// ── Core Agent Types ──────────────────────────────────────────────

/** Unique identifier for each section agent */
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

/** Startup characteristics identified by InputAnalyzer */
interface StartupCharacteristics {
  type: "marketplace" | "saas" | "e-commerce" | "fintech" | "healthtech"
    | "edtech" | "social" | "hardware" | "platform" | "api" | "agency" | "other";
  model: "b2b" | "b2c" | "b2b2c" | "d2c" | "marketplace" | "hybrid";
  complexity: "simple" | "moderate" | "complex" | "highly-complex";
  industry: string;           // e.g., "pet-care", "fintech", "healthcare"
  geography: string;          // e.g., "global", "us-only", "eu-focused"
  hasHardware: boolean;
  hasRegulatoryRequirements: boolean;
  isTwoSidedMarketplace: boolean;
  requiresIntegrations: boolean;
  estimatedTeamSize: number;
}

/** InputAnalyzer output */
interface InputAnalysisResult {
  originalIdea: string;
  characteristics: StartupCharacteristics;
  relevantSections: SectionId[];
  excludedSections: SectionId[];
  exclusionReasons: Record<SectionId, string>;
  estimatedComplexity: "low" | "medium" | "high";
  estimatedTokens: number;
  estimatedDurationSeconds: number;
}

/** Section agent definition — the core building block */
interface SectionAgentDefinition {
  id: SectionId;
  name: string;                    // Human-readable name
  description: string;             // What this section covers
  category: "strategy" | "market" | "financial" | "technical" | "operational";

  /** System prompt template — {idea}, {characteristics}, {dependencies} are interpolated */
  systemPrompt: string;

  /** What sections must be generated BEFORE this one */
  dependencies: SectionId[];

  /** Which characteristics make this section relevant (deterministic filter) */
  relevantFor: {
    types?: StartupCharacteristics["type"][];      // null/empty = always relevant
    models?: StartupCharacteristics["model"][];
    flags?: Array<keyof Pick<StartupCharacteristics,
      "hasHardware" | "hasRegulatoryRequirements" | "isTwoSidedMarketplace"
      | "requiresIntegrations">>;
  };

  /** Token budget estimate for generation */
  estimatedTokens: {
    input: number;   // system prompt + context
    output: number;  // expected section content
  };

  /** Output format specification */
  outputFormat: "markdown" | "json" | "structured-markdown";

  /** Whether this section supports refinement chat */
  chatEnabled: boolean;

  /** Max retries on failure */
  maxRetries: number;

  /** Timeout in seconds */
  timeoutSeconds: number;
}

/** Runtime state of a section agent during execution */
interface SectionAgentState {
  definition: SectionAgentDefinition;
  status: "pending" | "generating" | "completed" | "failed" | "skipped" | "retrying";
  result?: string;                    // Generated content (markdown/json)
  error?: string;                     // Error message if failed
  attempts: number;
  startedAt?: Date;
  completedAt?: Date;
  tokensUsed: { input: number; output: number };
  chatHistory: ChatMessage[];
}

/** A single chat message in section refinement */
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  tokensUsed?: number;
}

/** Workspace = the assembled analysis */
interface Workspace {
  id: string;
  createdAt: Date;
  updatedAt: Date;
  idea: string;
  analysis: InputAnalysisResult;
  sections: Record<SectionId, SectionAgentState>;
  globalChatHistory: ChatMessage[];  // workspace-level chat (not section-specific)
  metadata: {
    totalTokensUsed: number;
    generationDurationMs: number;
    phase: "generating" | "complete" | "partial-failure";
  };
}
```

### 2.2 Agent Lifecycle

```
                    ┌─────────────┐
                    │  Registered │  (SectionAgentDefinition in registry)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Routing   │  InputAnalyzer determines relevant sections
                    │  Selected   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Dependency │  Check if dependencies are met
                    │   Check     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Context    │  Inject workspace context into prompt
                    │  Assembly   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  LLM Call   │  Execute system prompt + context
                    │  (stream)   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Result     │  Parse, validate, store
                    │  Handling   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Complete   │  Section available for refinement
                    │  or Retry   │
                    └─────────────┘
```

---

## 3. Orchestration Strategy — Three Phases

### Phase 1: Sequential Generation

**Simplest possible approach. Generate one section at a time. Easiest to debug, lowest token cost risk.**

```
User Input
    │
    ▼
┌──────────────┐
│ InputAnalyzer │  ← Single LLM call
└──────┬───────┘
       │
       ▼
┌──────────────┐
│SectionRouter  │  ← Deterministic (no LLM)
└──────┬───────┘
       │
       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Section[0]   │───▶│ Section[1]   │───▶│ Section[2]   │───▶ ...
│ (LLM call)   │    │ (LLM call)   │    │ (LLM call)   │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
   [Store]             [Store]             [Store]
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Workspace   │  ← All sections assembled
                    │  Ready       │
                    └──────────────┘
```

**Implementation:**

```typescript
class SequentialOrchestrator {
  async generate(idea: string): Promise<Workspace> {
    // Step 1: Analyze input (1 LLM call)
    const analysis = await this.inputAnalyzer.analyze(idea);

    // Step 2: Route to sections (deterministic)
    const sections = this.sectionRouter.resolve(analysis);

    // Step 3: Generate each section sequentially
    const workspace = this.createWorkspace(idea, analysis);

    for (const sectionId of sections) {
      try {
        const result = await this.generateSection(workspace, sectionId);
        workspace.sections[sectionId] = result;
      } catch (error) {
        workspace.sections[sectionId] = { status: "failed", error: error.message };
      }
    }

    workspace.metadata.phase = "complete";
    return workspace;
  }

  private async generateSection(
    workspace: Workspace,
    sectionId: SectionId
  ): Promise<SectionAgentState> {
    const agent = this.registry.get(sectionId);
    const context = this.contextBuilder.build(workspace, sectionId);

    const result = await this.llmClient.generate({
      system: agent.systemPrompt,
      messages: [{ role: "user", content: context }],
      maxTokens: agent.estimatedTokens.output,
      timeout: agent.timeoutSeconds * 1000,
    });

    return {
      definition: agent,
      status: "completed",
      result: result.content,
      attempts: 1,
      startedAt: new Date(),
      completedAt: new Date(),
      tokensUsed: result.usage,
      chatHistory: [],
    };
  }
}
```

**Pros:** Simple, debuggable, predictable token usage
**Cons:** Slow (N sequential LLM calls), total time = sum of all sections

---

### Phase 2: Parallel Generation

**Generate independent sections simultaneously. Sections with no dependencies on each other run in parallel.**

```
User Input
    │
    ▼
┌──────────────┐
│ InputAnalyzer │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│SectionRouter  │
└──────┬───────┘
       │
       ├────────────────────────────────────────┐
       │                                        │
       ▼                                        ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Wave 0:    │  │  Wave 0:    │  │  Wave 0:    │  ← No dependencies
│ ProblemStmt │  │  Solution   │  │  TargetCust │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────┬───────┴────────┬───────┘
                │                │
                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │  Wave 1:    │  │  Wave 1:    │  │  Wave 1:    │  ← Depend on Wave 0
       │  Personas   │  │  TAM/SAM    │  │  Competitors│
       └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
              │                │                │
              └────────┬───────┴────────┬───────┘
                       │                │
                       ▼                ▼
              ┌─────────────┐  ┌─────────────┐
              │  Wave 2:    │  │  Wave 2:    │  ← Depend on Wave 0+1
              │  Revenue    │  │  GTM        │
              └─────────────┘  └─────────────┘
```

**Implementation:**

```typescript
class ParallelOrchestrator {
  private maxConcurrent = 5;  // LLM call concurrency limit

  async generate(idea: string): Promise<Workspace> {
    const analysis = await this.inputAnalyzer.analyze(idea);
    const sections = this.sectionRouter.resolve(analysis);
    const waves = this.dependencyGraph.topologicalWaves(sections);
    const workspace = this.createWorkspace(idea, analysis);

    for (const wave of waves) {
      // All sections in a wave have their dependencies met
      const results = await Promise.allSettled(
        wave.map(sectionId => this.generateSection(workspace, sectionId))
      );

      for (let i = 0; i < wave.length; i++) {
        const sectionId = wave[i];
        const result = results[i];
        if (result.status === "fulfilled") {
          workspace.sections[sectionId] = result.value;
        } else {
          workspace.sections[sectionId] = {
            definition: this.registry.get(sectionId),
            status: "failed",
            error: result.reason?.message ?? "Unknown error",
            attempts: 1,
            tokensUsed: { input: 0, output: 0 },
            chatHistory: [],
          };
        }
      }
    }

    workspace.metadata.phase = "complete";
    return workspace;
  }
}
```

**Wave resolution example for "Airbnb for pets":**

| Wave | Sections | Why this wave |
|------|----------|---------------|
| 0 | Problem Statement, Solution, Target Customers | No dependencies |
| 1 | Customer Personas, TAM/SAM/SOM, Competitor Analysis, SWOT | Depend on Wave 0 outputs |
| 2 | Business Model Canvas, Revenue Model, Pricing Strategy | Depend on Wave 0+1 |
| 3 | Go-to-Market, MVP Definition, Feature Prioritization | Depend on Wave 0+1+2 |
| 4 | Technical Architecture, Tech Stack, Database, API, UI Sitemap | Depend on MVP/Features |
| 5 | Product Roadmap, Risk Analysis, Financial Assumptions, Launch Checklist | Depend on everything |

**Pros:** Much faster (time = slowest wave, not sum of all), respects dependencies
**Cons:** Higher peak token usage, harder to debug, need concurrency control

---

### Phase 3: Full Multi-Agent with Inter-Agent Communication

**Agents can request data from other agents at runtime. Agents discover what they need dynamically.**

```
┌─────────────────────────────────────────────────────────┐
│                    Message Bus                          │
│  (pub/sub for inter-agent communication)                │
└────┬──────────┬──────────┬──────────┬──────────┬────────┘
     │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│ Problem ││Solution ││Revenue  ││Financial││ Tech    │
│ Statement││ Agent   ││ Model   ││Assumpts ││ Arch    │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
     │          │          │          │          │
     └──────────┴──────────┴──────────┴──────────┘
                           │
                    ┌──────▼──────┐
                    │   Shared    │
                    │   Context   │
                    │   Store     │
                    └─────────────┘
```

**New interface for Phase 3:**

```typescript
/** Message types for inter-agent communication */
interface AgentMessage {
  type: "request" | "response" | "broadcast";
  from: SectionId;
  to: SectionId | "all";
  requestId: string;
  payload: {
    query: string;           // What data is being requested
    context?: string;        // Additional context for the request
  };
  timestamp: Date;
}

/** Agent can request data from other agents */
interface AgentCapabilities {
  canRequest: SectionId[];   // Which agents this agent can ask for data
  canProvide: string[];      // What data this agent can provide to others
}

/** Phase 3 agent definition extends base */
interface Phase3AgentDefinition extends SectionAgentDefinition {
  capabilities: AgentCapabilities;

  /** System prompt includes instructions for inter-agent communication */
  communicationPrompt: string;

  /** How to handle requests from other agents */
  onRequest?: (request: AgentMessage) => Promise<string>;
}

/** Message bus for agent communication */
interface IMessageBus {
  publish(message: AgentMessage): void;
  subscribe(sectionId: SectionId, handler: (msg: AgentMessage) => void): void;
  request(from: SectionId, to: SectionId, query: string): Promise<string>;
}
```

**Example inter-agent flow:**

```
Revenue Model Agent needs:
  - Business Model Canvas output → requests from BM Canvas agent
  - Customer personas → requests from Personas agent
  - TAM/SAM/SOM → requests from Market Size agent

Financial Assumptions Agent needs:
  - Revenue Model output → requests from Revenue Model agent
  - Pricing Strategy → requests from Pricing agent
  - Cost assumptions → generates its own

Technical Architecture Agent needs:
  - MVP Definition → requests from MVP agent
  - Feature prioritization → requests from Features agent
  - Team size estimate → requests from InputAnalyzer
```

**Evolution path:** Phase 3 is a future enhancement. The agent definitions already include dependency metadata — Phase 3 just makes those dependencies dynamic and runtime-resolved.

---

## 4. Agent Registry

### 4.1 Registry Implementation

```typescript
class AgentRegistry {
  private agents: Map<SectionId, SectionAgentDefinition> = new Map();

  /** Register a single agent */
  register(definition: SectionAgentDefinition): void {
    // Validate dependencies exist
    for (const dep of definition.dependencies) {
      if (!this.agents.has(dep)) {
        throw new Error(
          `Agent "${definition.id}" depends on "${dep}" which is not registered`
        );
      }
    }
    this.agents.set(definition.id, definition);
  }

  /** Register multiple agents at once */
  registerAll(definitions: SectionAgentDefinition[]): void {
    // Sort by dependency count to catch errors early
    const sorted = [...definitions].sort(
      (a, b) => a.dependencies.length - b.dependencies.length
    );
    for (const def of sorted) {
      this.register(def);
    }
  }

  /** Get agent by ID */
  get(id: SectionId): SectionAgentDefinition {
    const agent = this.agents.get(id);
    if (!agent) throw new Error(`Agent "${id}" not found in registry`);
    return agent;
  }

  /** Get all agents */
  getAll(): SectionAgentDefinition[] {
    return Array.from(this.agents.values());
  }

  /** Get agents by category */
  getByCategory(category: SectionAgentDefinition["category"]): SectionAgentDefinition[] {
    return this.getAll().filter(a => a.category === category);
  }

  /** Check if all dependencies for a set of agents are met */
  validateDependencies(sectionIds: SectionId[]): { valid: boolean; missing: SectionId[] } {
    const available = new Set(sectionIds);
    const missing: SectionId[] = [];
    for (const id of sectionIds) {
      const agent = this.get(id);
      for (const dep of agent.dependencies) {
        if (!available.has(dep)) missing.push(dep);
      }
    }
    return { valid: missing.length === 0, missing };
  }
}
```

### 4.2 Agent Definition File Structure

Agents are defined as separate files for easy addition/replacement:

```
agents/
  registry.ts              # Registry singleton + loading logic
  definitions/
    executive-summary.ts
    problem-statement.ts
    solution.ts
    target-customers.ts
    customer-personas.ts
    tam-sam-som.ts
    competitor-analysis.ts
    swot-analysis.ts
    business-model-canvas.ts
    revenue-model.ts
    pricing-strategy.ts
    go-to-market-strategy.ts
    mvp-definition.ts
    feature-prioritization.ts
    technical-architecture.ts
    suggested-tech-stack.ts
    database-design.ts
    api-overview.ts
    ui-sitemap.ts
    product-roadmap.ts
    risk-analysis.ts
    financial-assumptions.ts
    launch-checklist.ts
    _templates/             # Prompt templates
      marketplace.md
      saas.md
      ecommerce.md
```

### 4.3 Example Agent Definition

```typescript
// agents/definitions/revenue-model.ts

import { SectionAgentDefinition } from "../types";

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

### Revenue Projections (Qualitative)
- Year 1: [range + reasoning]
- Year 2: [range + reasoning]
- Year 3: [range + reasoning]

Be specific to THIS startup. Reference the characteristics and dependencies above.
Use ranges when exact numbers are speculative. Always explain your reasoning.`,

  dependencies: ["business-model-canvas", "target-customers", "tam-sam-som"],

  relevantFor: {
    // All startups need revenue modeling
  },

  estimatedTokens: {
    input: 2500,
    output: 1500,
  },

  outputFormat: "markdown",
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
```

---

## 5. Routing System

### 5.1 InputAnalyzer

```typescript
/** What InputAnalyzer produces */
interface InputAnalysisResult {
  originalIdea: string;
  characteristics: StartupCharacteristics;
  relevantSections: SectionId[];
  excludedSections: SectionId[];
  exclusionReasons: Record<SectionId, string>;
  estimatedComplexity: "low" | "medium" | "high";
  estimatedTokens: number;
  estimatedDurationSeconds: number;
}

class InputAnalyzer {
  private systemPrompt = `You are a startup analysis routing engine. Your job is to analyze a startup idea and determine its characteristics.

Given a startup idea, output a JSON object with:
1. type: The startup type (one of: marketplace, saas, e-commerce, fintech, healthtech, edtech, social, hardware, platform, api, agency, other)
2. model: Business model (one of: b2b, b2c, b2b2c, d2c, marketplace, hybrid)
3. complexity: Technical complexity (simple, moderate, complex, highly-complex)
4. industry: Specific industry (e.g., "pet-care", "fintech", "healthcare")
5. geography: Target geography (e.g., "global", "us-only")
6. hasHardware: boolean — does this involve physical hardware?
7. hasRegulatoryRequirements: boolean — regulated industry?
8. isTwoSidedMarketplace: boolean — two distinct user groups?
9. requiresIntegrations: boolean — needs third-party APIs/services?
10. estimatedTeamSize: number — rough team size for MVP

Output ONLY valid JSON. No explanation.`;

  async analyze(idea: string): Promise<InputAnalysisResult> {
    const response = await this.llmClient.generate({
      system: this.systemPrompt,
      messages: [{ role: "user", content: idea }],
      maxTokens: 500,
      temperature: 0.1,  // Low temperature for consistent classification
    });

    const characteristics: StartupCharacteristics = JSON.parse(response.content);
    const relevantSections = this.resolveSections(characteristics);

    return {
      originalIdea: idea,
      characteristics,
      relevantSections,
      excludedSections: ALL_SECTIONS.filter(s => !relevantSections.includes(s)),
      exclusionReasons: this.buildExclusionReasons(characteristics, relevantSections),
      estimatedComplexity: this.estimateComplexity(characteristics),
      estimatedTokens: this.estimateTokens(relevantSections),
      estimatedDurationSeconds: this.estimateDuration(relevantSections),
    };
  }
}
```

### 5.2 Section Router (Deterministic, No LLM)

```typescript
class SectionRouter {
  resolve(analysis: InputAnalysisResult): SectionId[] {
    const allAgents = this.registry.getAll();
    const relevant: SectionId[] = [];

    for (const agent of allAgents) {
      if (this.isRelevant(agent, analysis.characteristics)) {
        relevant.push(agent.id);
      }
    }

    return relevant;
  }

  private isRelevant(
    agent: SectionAgentDefinition,
    chars: StartupCharacteristics
  ): boolean {
    const { relevantFor } = agent;

    // Empty relevantFor = always relevant
    if (!relevantFor.types?.length && !relevantFor.models?.length && !relevantFor.flags?.length) {
      return true;
    }

    let match = false;

    if (relevantFor.types?.length) {
      match = match || relevantFor.types.includes(chars.type);
    }
    if (relevantFor.models?.length) {
      match = match || relevantFor.models.includes(chars.model);
    }
    if (relevantFor.flags?.length) {
      match = match || relevantFor.flags.some(flag => chars[flag]);
    }

    return match;
  }
}
```

### 5.3 Section Relevance Map

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
| Database Design | complexity != "simple" AND requiresIntegrations or complexity == "complex" or "highly-complex" |
| API Overview | type == "saas" OR type == "platform" OR type == "api" OR type == "marketplace" |
| UI Sitemap | type != "api" AND type != "agency" |
| Product Roadmap | Always |
| Risk Analysis | complexity != "simple" |
| Financial Assumptions | Not "agency" type |
| Launch Checklist | Always |

### 5.4 Dependency Graph

```
executive-summary ──────────────────────────────────────┐
problem-statement ─────────────────────────────────────┤
solution ──────────────────────────────────────────────┤
target-customers ─────┬────────────────────────────────┤
                      │                                 │
customer-personas ◄───┘                                 │
tam-sam-som ◄──────────────────────────────────────────┤
competitor-analysis ◄──────────────────────────────────┤
swot-analysis ◄────────────────────────────────────────┤
business-model-canvas ◄────────────────────────────────┤
                      │                                 │
revenue-model ◄───────┼── business-model-canvas         │
                      ├── target-customers              │
                      └── tam-sam-som                   │
                      │                                 │
pricing-strategy ◄────┼── revenue-model                 │
                      └── competitor-analysis           │
                      │                                 │
go-to-market-strategy ◄─ target-customers               │
                      ├── competitor-analysis           │
                      └── revenue-model                 │
                      │                                 │
mvp-definition ◄──────┼── solution                      │
                      └── feature-prioritization        │
                      │                                 │
feature-prioritization ◄─ solution                      │
                      ├── customer-personas             │
                      └── competitor-analysis           │
                      │                                 │
technical-architecture ◄─ mvp-definition                │
                      └── feature-prioritization        │
                      │                                 │
suggested-tech-stack ◄── technical-architecture         │
database-design ◄────── technical-architecture          │
api-overview ◄───────── technical-architecture          │
ui-sitemap ◄─────────── mvp-definition                  │
                      │                                 │
product-roadmap ◄──────┼── mvp-definition               │
                      ├── feature-prioritization        │
                      └── technical-architecture        │
                      │                                 │
risk-analysis ◄────────┼── all financial sections       │
                      └── competitor-analysis           │
                      │                                 │
financial-assumptions ◄─ revenue-model                  │
                      ├── pricing-strategy              │
                      └── business-model-canvas         │
                      │                                 │
launch-checklist ◄─────┼── mvp-definition               │
                      └── technical-architecture        │
```

### 5.5 Topological Wave Resolution

```typescript
class DependencyGraph {
  topologicalWaves(sectionIds: SectionId[]): SectionId[][] {
    const agents = sectionIds.map(id => this.registry.get(id));
    const resolved = new Set<SectionId>();
    const waves: SectionId[][] = [];

    while (resolved.size < agents.length) {
      const wave: SectionId[] = [];

      for (const agent of agents) {
        if (resolved.has(agent.id)) continue;

        const depsMet = agent.dependencies.every(
          dep => resolved.has(dep) || !sectionIds.includes(dep)
        );

        if (depsMet) {
          wave.push(agent.id);
        }
      }

      if (wave.length === 0) {
        throw new Error("Circular dependency detected");
      }

      waves.push(wave);
      wave.forEach(id => resolved.add(id));
    }

    return waves;
  }
}
```

---

## 6. Execution Pipeline

### 6.1 LLM Client Interface

```typescript
interface LLMClient {
  generate(params: LLMGenerateParams): Promise<LLMResult>;
  stream?(params: LLMGenerateParams): AsyncIterable<LLMChunk>;
}

interface LLMGenerateParams {
  system: string;
  messages: Array<{ role: "user" | "assistant"; content: string }>;
  maxTokens: number;
  temperature?: number;
  timeout?: number;
}

interface LLMResult {
  content: string;
  usage: { input: number; output: number };
  model: string;
  finishReason: "stop" | "length" | "timeout" | "error";
}

interface LLMChunk {
  delta: string;        // Incremental text
  usage?: { input: number; output: number };  // Only on final chunk
}
```

### 6.2 Context Builder

```typescript
class ContextBuilder {
  build(workspace: Workspace, sectionId: SectionId): string {
    const agent = workspace.sections[sectionId]?.definition
      ?? this.registry.get(sectionId);

    const parts: string[] = [];

    // 1. Core idea
    parts.push(`## Startup Idea\n${workspace.idea}`);

    // 2. Characteristics
    parts.push(`## Characteristics\n${JSON.stringify(workspace.analysis.characteristics, null, 2)}`);

    // 3. Dependencies (already generated sections)
    if (agent.dependencies.length > 0) {
      parts.push("## Preceding Sections (use as context)\n");
      for (const depId of agent.dependencies) {
        const depState = workspace.sections[depId];
        if (depState?.status === "completed" && depState.result) {
          parts.push(`### ${depState.definition.name}\n${depState.result}\n`);
        }
      }
    }

    // 4. For refinement: chat history
    const state = workspace.sections[sectionId];
    if (state?.chatHistory.length) {
      parts.push("## Previous Refinement Conversation\n");
      for (const msg of state.chatHistory) {
        parts.push(`**${msg.role}:** ${msg.content}\n`);
      }
    }

    return parts.join("\n\n");
  }
}
```

### 6.3 Streaming Results

```typescript
/** Server-Sent Events for real-time section delivery */
interface StreamingOrchestrator {
  /** Emit events as sections complete */
  generate(idea: string): AsyncGenerator<OrchestrationEvent>;
}

type OrchestrationEvent =
  | { type: "analysis-complete"; data: InputAnalysisResult }
  | { type: "section-started"; sectionId: SectionId }
  | { type: "section-token"; sectionId: SectionId; delta: string }
  | { type: "section-complete"; sectionId: SectionId; result: string }
  | { type: "section-failed"; sectionId: SectionId; error: string }
  | { type: "generation-complete"; workspace: Workspace }
  | { type: "token-warning"; current: number; limit: number };

// Server-side (Node.js)
async function* generateStream(idea: string): AsyncGenerator<OrchestrationEvent> {
  const analysis = await inputAnalyzer.analyze(idea);
  yield { type: "analysis-complete", data: analysis };

  const sections = sectionRouter.resolve(analysis);
  const waves = dependencyGraph.topologicalWaves(sections);

  for (const wave of waves) {
    const generators = wave.map(sectionId => generateSectionStream(sectionId));

    // Merge parallel streams
    for await (const event of mergeAsync(generators)) {
      yield event;
    }
  }
}

// Client-side (browser)
const eventSource = new EventSource(`/api/generate?idea=${encodeURIComponent(idea)}`);
eventSource.onmessage = (event) => {
  const data: OrchestrationEvent = JSON.parse(event.data);
  switch (data.type) {
    case "section-started":
      showSpinner(data.sectionId);
      break;
    case "section-token":
      appendToSection(data.sectionId, data.delta);
      break;
    case "section-complete":
      finalizeSection(data.sectionId, data.result);
      break;
  }
};
```

---

## 7. Memory & Context Design

### 7.1 Context Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Workspace Context                      │
│  (injected into every agent's system prompt)             │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Original Idea                                   │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Startup Characteristics                         │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Generated Sections (completed so far)           │    │
│  │  - Executive Summary ✓                           │    │
│  │  - Problem Statement ✓                           │    │
│  │  - Solution ✓                                    │    │
│  │  ...                                             │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                Section Chat Context                      │
│  (per-section refinement history)                        │
│                                                          │
│  Section: "revenue-model"                                │
│  Chat History:                                           │
│    user: "Add a subscription tier"                       │
│    assistant: "I've added a subscription tier..."        │
│    user: "What about enterprise pricing?"                │
│    assistant: "For enterprise, I'd recommend..."         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                Serializable State                         │
│  (persisted to filesystem for local, DB for SaaS)        │
│                                                          │
│  workspace-{id}.json:                                    │
│    - id, createdAt, idea                                 │
│    - analysis (InputAnalysisResult)                      │
│    - sections (Record<SectionId, SectionAgentState>)     │
│    - globalChatHistory                                   │
│    - metadata                                            │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Storage Interface

```typescript
interface WorkspaceStore {
  /** Save workspace state (atomic write) */
  save(workspace: Workspace): Promise<void>;

  /** Load workspace by ID */
  load(id: string): Promise<Workspace | null>;

  /** List all workspaces (summary only) */
  list(): Promise<WorkspaceSummary[]>;

  /** Delete workspace */
  delete(id: string): Promise<void>;
}

interface WorkspaceSummary {
  id: string;
  idea: string;
  createdAt: Date;
  updatedAt: Date;
  sectionCount: number;
  totalTokens: number;
}

/** Local filesystem implementation */
class FilesystemWorkspaceStore implements WorkspaceStore {
  private baseDir: string;

  constructor(baseDir: string) {
    this.baseDir = baseDir;
  }

  async save(workspace: Workspace): Promise<void> {
    const dir = path.join(this.baseDir, workspace.id);
    await fs.mkdir(dir, { recursive: true });

    // Atomic write: write to temp, then rename
    const tmpPath = path.join(dir, "workspace.json.tmp");
    const finalPath = path.join(dir, "workspace.json");
    await fs.writeFile(tmpPath, JSON.stringify(workspace, null, 2));
    await fs.rename(tmpPath, finalPath);
  }

  async load(id: string): Promise<Workspace | null> {
    const filePath = path.join(this.baseDir, id, "workspace.json");
    try {
      const data = await fs.readFile(filePath, "utf-8");
      return JSON.parse(data);
    } catch {
      return null;
    }
  }

  async list(): Promise<WorkspaceSummary[]> {
    const entries = await fs.readdir(this.baseDir);
    const summaries: WorkspaceSummary[] = [];
    for (const entry of entries) {
      const workspace = await this.load(entry);
      if (workspace) {
        summaries.push({
          id: workspace.id,
          idea: workspace.idea,
          createdAt: workspace.createdAt,
          updatedAt: workspace.updatedAt,
          sectionCount: Object.keys(workspace.sections).length,
          totalTokens: workspace.metadata.totalTokensUsed,
        });
      }
    }
    return summaries;
  }
}
```

### 7.3 Refinement Chat Flow

```typescript
class SectionChatHandler {
  async refine(
    workspaceId: string,
    sectionId: SectionId,
    userMessage: string
  ): Promise<AsyncGenerator<string>> {
    const workspace = await this.store.load(workspaceId);
    if (!workspace) throw new Error("Workspace not found");

    const state = workspace.sections[sectionId];
    if (!state?.definition.chatEnabled) {
      throw new Error(`Section "${sectionId}" does not support chat refinement`);
    }

    // Add user message to history
    state.chatHistory.push({
      role: "user",
      content: userMessage,
      timestamp: new Date(),
    });

    // Build context: workspace + chat history
    const context = this.contextBuilder.build(workspace, sectionId);
    const agent = state.definition;

    // Stream response
    const stream = this.llmClient.stream!({
      system: agent.systemPrompt,
      messages: state.chatHistory.map(m => ({ role: m.role, content: m.content })),
      maxTokens: agent.estimatedTokens.output,
      temperature: 0.3,
    });

    let fullResponse = "";
    for await (const chunk of stream) {
      fullResponse += chunk.delta;
      yield chunk.delta;
    }

    // Store assistant response
    state.chatHistory.push({
      role: "assistant",
      content: fullResponse,
      timestamp: new Date(),
    });

    // Update section result with refined content
    state.result = fullResponse;

    // Persist
    workspace.updatedAt = new Date();
    await this.store.save(workspace);
  }
}
```

---

## 8. Token Management

### 8.1 Token Estimation

```typescript
interface TokenBudget {
  inputPerAgent: Record<SectionId, number>;
  outputPerAgent: Record<SectionId, number>;
  totalBudget: number;          // Max tokens for entire analysis
  warningThreshold: number;     // Warn at 80% usage
}

/** Estimated tokens per section (tunable) */
const TOKEN_ESTIMATES: Record<SectionId, { input: number; output: number }> = {
  "executive-summary":       { input: 1500, output: 800 },
  "problem-statement":       { input: 1200, output: 600 },
  "solution":                { input: 1500, output: 800 },
  "target-customers":        { input: 1200, output: 600 },
  "customer-personas":       { input: 2000, output: 1000 },
  "tam-sam-som":             { input: 2000, output: 1200 },
  "competitor-analysis":     { input: 2500, output: 1500 },
  "swot-analysis":           { input: 2000, output: 1000 },
  "business-model-canvas":   { input: 2500, output: 1500 },
  "revenue-model":           { input: 2500, output: 1200 },
  "pricing-strategy":        { input: 2500, output: 1000 },
  "go-to-market-strategy":   { input: 2500, output: 1500 },
  "mvp-definition":          { input: 2000, output: 1000 },
  "feature-prioritization":  { input: 2500, output: 1200 },
  "technical-architecture":  { input: 3000, output: 2000 },
  "suggested-tech-stack":    { input: 2500, output: 1500 },
  "database-design":         { input: 3000, output: 2000 },
  "api-overview":            { input: 3000, output: 1500 },
  "ui-sitemap":              { input: 2000, output: 1000 },
  "product-roadmap":         { input: 3000, output: 1500 },
  "risk-analysis":           { input: 2500, output: 1200 },
  "financial-assumptions":   { input: 3000, output: 1500 },
  "launch-checklist":        { input: 2500, output: 1200 },
};

class TokenManager {
  private used = 0;
  private budget: number;
  private warningThreshold: number;
  private onWarning?: (current: number, limit: number) => void;

  constructor(budget: number, warningPercent = 0.8) {
    this.budget = budget;
    this.warningThreshold = budget * warningPercent;
  }

  estimateForSections(sectionIds: SectionId[]): number {
    let total = 0;
    for (const id of sectionIds) {
      const est = TOKEN_ESTIMATES[id];
      total += est.input + est.output;
    }
    // Add ~15% for context injection overhead
    return Math.ceil(total * 1.15);
  }

  track(sectionId: SectionId, usage: { input: number; output: number }): void {
    this.used += usage.input + usage.output;

    if (this.used >= this.warningThreshold && this.onWarning) {
      this.onWarning(this.used, this.budget);
    }
  }

  canAfford(sectionId: SectionId): boolean {
    const est = TOKEN_ESTIMATES[sectionId];
    return this.used + est.input + est.output <= this.budget;
  }

  getRemaining(): number {
    return Math.max(0, this.budget - this.used);
  }

  getUsageReport(): { used: number; budget: number; remaining: number; percentUsed: number } {
    return {
      used: this.used,
      budget: this.budget,
      remaining: this.getRemaining(),
      percentUsed: Math.round((this.used / this.budget) * 100),
    };
  }
}
```

### 8.2 Caching Strategy

```typescript
/** Cache identical ideas to avoid re-analysis */
class AnalysisCache {
  private cache: Map<string, InputAnalysisResult> = new Map();

  /** Generate cache key from normalized idea text */
  private key(idea: string): string {
    return idea.toLowerCase().trim().replace(/\s+/g, " ");
  }

  get(idea: string): InputAnalysisResult | undefined {
    return this.cache.get(this.key(idea));
  }

  set(idea: string, result: InputAnalysisResult): void {
    this.cache.set(this.key(idea), result);
  }

  has(idea: string): boolean {
    return this.cache.has(this.key(idea));
  }
}
```

---

## 9. Error Handling

### 9.1 Error Types

```typescript
type AgentError =
  | { type: "timeout"; sectionId: SectionId; timeoutMs: number }
  | { type: "llm-error"; sectionId: SectionId; message: string; code?: string }
  | { type: "parse-error"; sectionId: SectionId; raw: string; expected: string }
  | { type: "dependency-failed"; sectionId: SectionId; failedDeps: SectionId[] }
  | { type: "budget-exceeded"; sectionId: SectionId; remaining: number; required: number }
  | { type: "circular-dependency"; cycle: SectionId[] };
```

### 9.2 Retry Logic

```typescript
class RetryHandler {
  private maxRetries = 2;
  private baseDelayMs = 1000;

  async withRetry<T>(
    fn: () => Promise<T>,
    sectionId: SectionId,
    maxRetries?: number
  ): Promise<T> {
    const retries = maxRetries ?? this.maxRetries;
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;

        if (attempt < retries) {
          // Exponential backoff with jitter
          const delay = this.baseDelayMs * Math.pow(2, attempt)
            + Math.random() * 500;
          await sleep(delay);
        }
      }
    }

    throw lastError;
  }
}
```

### 9.3 Graceful Degradation

```typescript
class GracefulOrchestrator {
  async generate(idea: string): Promise<Workspace> {
    const analysis = await this.inputAnalyzer.analyze(idea);
    const sections = this.sectionRouter.resolve(analysis);
    const waves = this.dependencyGraph.topologicalWaves(sections);
    const workspace = this.createWorkspace(idea, analysis);

    const failed: SectionId[] = [];

    for (const wave of waves) {
      const results = await Promise.allSettled(
        wave.map(sectionId =>
          this.retryHandler.withRetry(
            () => this.generateSection(workspace, sectionId),
            sectionId
          )
        )
      );

      for (let i = 0; i < wave.length; i++) {
        const sectionId = wave[i];
        const result = results[i];

        if (result.status === "fulfilled") {
          workspace.sections[sectionId] = result.value;
        } else {
          failed.push(sectionId);
          workspace.sections[sectionId] = {
            definition: this.registry.get(sectionId),
            status: "failed",
            error: result.reason?.message ?? "Unknown error",
            attempts: 3,
            tokensUsed: { input: 0, output: 0 },
            chatHistory: [],
          };
          // Log but continue — don't abort the pipeline
          console.error(`Section "${sectionId}" failed: ${result.reason}`);
        }
      }

      // Skip next waves that depend on failed sections
      // (their dependencies aren't met)
      for (const futureWave of waves.slice(waves.indexOf(wave) + 1)) {
        for (const futureSection of futureWave) {
          const agent = this.registry.get(futureSection);
          const depsFailed = agent.dependencies.some(dep => failed.includes(dep));
          if (depsFailed && !workspace.sections[futureSection]) {
            workspace.sections[futureSection] = {
              definition: agent,
              status: "skipped",
              error: `Skipped: dependency "${agent.dependencies.find(d => failed.includes(d))}" failed`,
              attempts: 0,
              tokensUsed: { input: 0, output: 0 },
              chatHistory: [],
            };
            failed.push(futureSection);
          }
        }
      }
    }

    workspace.metadata.phase = failed.length > 0 ? "partial-failure" : "complete";
    return workspace;
  }
}
```

---

## 10. Complete Phase Evolution Path

### Phase 1 → Phase 2 Migration Checklist

1. ✅ Add `DependencyGraph.topologicalWaves()` method
2. ✅ Change `for` loop to `Promise.allSettled` per wave
3. ✅ Add concurrency limit (`maxConcurrent`)
4. ✅ Update streaming to merge parallel outputs
5. ✅ No changes to agent definitions needed — dependencies already declared

### Phase 2 → Phase 3 Migration Checklist

1. Add `IMessageBus` implementation
2. Add `capabilities` field to `SectionAgentDefinition`
3. Update system prompts with inter-agent communication instructions
4. Add `onRequest` handlers to agent definitions
5. Update `ContextBuilder` to include data from other agents via message bus
6. Add `communicationPrompt` to agent definitions

### Summary

| Feature | Phase 1 | Phase 2 | Phase 3 |
|---------|---------|---------|---------|
| Generation | Sequential | Wave-parallel | Fully parallel + dynamic |
| Dependencies | Pre-computed | Pre-computed waves | Runtime resolution |
| Agent communication | None | Via shared context | Via message bus |
| Complexity | Low | Medium | High |
| Token efficiency | Highest | High | Medium (overhead from messages) |
| Speed | Slowest | Fast | Fastest |
| Debugging | Easiest | Moderate | Hardest |

---

## 11. File Structure

```
src/
  orchestrator/
    types.ts                          # All TypeScript interfaces
    registry.ts                       # AgentRegistry class
    input-analyzer.ts                 # InputAnalyzer (LLM call)
    section-router.ts                 # SectionRouter (deterministic)
    dependency-graph.ts               # DependencyGraph + topological sort
    context-builder.ts                # ContextBuilder (prompt assembly)
    token-manager.ts                  # TokenManager + TOKEN_ESTIMATES
    sequential-orchestrator.ts        # Phase 1 implementation
    parallel-orchestrator.ts          # Phase 2 implementation
    graceful-orchestrator.ts          # Error handling + degradation
    streaming.ts                      # SSE/streaming support
    workspace-store.ts                # Persistence (filesystem/DB)
    section-chat.ts                   # Refinement chat handler

  agents/
    definitions/
      executive-summary.ts
      problem-statement.ts
      ... (22 agent definition files)
    templates/                        # System prompt templates
      base.md
      marketplace.md
      saas.md
    registry.ts                       # Auto-loads all definitions

  llm/
    client.ts                         # LLMClient interface
    openai-client.ts                  # OpenAI/compatible implementation
    cache.ts                          # Response caching

  api/
    routes/
      analyze.ts                      # POST /api/analyze — start generation
      stream.ts                       # GET /api/stream/:id — SSE events
      workspace.ts                    # CRUD /api/workspace/:id
      chat.ts                         # POST /api/workspace/:id/section/:sectionId/chat

  storage/
    filesystem-store.ts               # Local implementation
    database-store.ts                 # Future SaaS implementation
```

---

## 12. Adding a New Section Agent

To add a new section (e.g., "sustainability-analysis"):

1. Create `src/agents/definitions/sustainability-analysis.ts`:

```typescript
export const sustainabilityAgent: SectionAgentDefinition = {
  id: "sustainability-analysis",
  name: "Sustainability Analysis",
  description: "Environmental and social impact assessment",
  category: "operational",
  systemPrompt: `...`,
  dependencies: ["solution", "business-model-canvas"],
  relevantFor: {
    flags: ["hasRegulatoryRequirements"],
    // Also relevant for certain industries
    types: ["healthtech", "fintech"],
  },
  estimatedTokens: { input: 2000, output: 1200 },
  outputFormat: "markdown",
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
```

2. Add `"sustainability-analysis"` to the `SectionId` union type in `types.ts`
3. Add entry to `TOKEN_ESTIMATES` in `token-manager.ts`
4. Update the `SectionRouter.relevantFor` map in `section-router.ts`
5. Add dependency edges to `dependency-graph.ts`
6. Done — the agent is automatically discovered and used

No changes needed to the orchestrator, context builder, or storage layer.
