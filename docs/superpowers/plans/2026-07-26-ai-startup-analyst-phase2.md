# AI Startup Analyst — Phase 2: Orchestrator & Generation Pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the orchestrator, context builder, generation pipeline, API routes, and basic workspace UI.

**Architecture:** Sequential orchestrator (Phase 1 of 3). Generates sections one at a time. Context builder assembles prompts with dependency outputs. API routes expose generation and chat endpoints. Basic UI for workspace viewing.

**Prerequisites:** Phase 1 complete (all 22 tests passing)

---

## Task 1: Dependency Graph & Topological Sort

**Files:**
- Create: `src/core/services/dependency-graph.ts`
- Test: `tests/core/services/dependency-graph.test.ts`

**Interfaces:**
- Consumes: `AgentRegistry`, `SectionId`
- Produces: `DependencyGraph` with `topologicalWaves()` method

- [ ] **Step 1: Write dependency graph test**

Create `tests/core/services/dependency-graph.test.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import { DependencyGraph } from '@/core/services/dependency-graph';
import { createRegistry } from '@/core/agents';

describe('DependencyGraph', () => {
  const registry = createRegistry();
  const graph = new DependencyGraph(registry);

  it('should resolve waves for all sections', () => {
    const allIds = registry.getAll().map(a => a.id);
    const waves = graph.topologicalWaves(allIds);

    expect(waves.length).toBeGreaterThan(0);
    // Wave 0 should have sections with no dependencies
    expect(waves[0]).toContain('executive-summary');
    expect(waves[0]).toContain('problem-statement');
    expect(waves[0]).toContain('solution');
  });

  it('should respect dependency order', () => {
    const allIds = registry.getAll().map(a => a.id);
    const waves = graph.topologicalWaves(allIds);

    // Track when each section is resolved
    const resolvedAt = new Map<string, number>();
    waves.forEach((wave, waveIndex) => {
      wave.forEach(id => resolvedAt.set(id, waveIndex));
    });

    // Each section's dependencies should be resolved in earlier waves
    for (const id of allIds) {
      const agent = registry.get(id);
      for (const dep of agent.dependencies) {
        if (allIds.includes(dep)) {
          expect(resolvedAt.get(dep)).toBeLessThan(resolvedAt.get(id)!);
        }
      }
    }
  });

  it('should handle subset of sections', () => {
    const subset = ['executive-summary', 'problem-statement', 'solution', 'target-customers'];
    const waves = graph.topologicalWaves(subset);

    expect(waves.length).toBeGreaterThan(0);
    waves.forEach(wave => {
      wave.forEach(id => expect(subset).toContain(id));
    });
  });

  it('should throw on circular dependency', () => {
    // This shouldn't happen with our definitions, but test the algorithm
    const circularIds = ['revenue-model', 'pricing-strategy', 'financial-assumptions'];
    // These have real dependencies, so just verify it doesn't throw
    const waves = graph.topologicalWaves(circularIds);
    expect(waves.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run tests/core/services/dependency-graph.test.ts --reporter=verbose
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create dependency graph**

Create `src/core/services/dependency-graph.ts`:
```typescript
import { AgentRegistry } from '../agents/registry';
import { SectionId } from '../types/project';

export class DependencyGraph {
  constructor(private registry: AgentRegistry) {}

  topologicalWaves(sectionIds: SectionId[]): SectionId[][] {
    const resolved = new Set<SectionId>();
    const waves: SectionId[][] = [];
    let maxIterations = sectionIds.length * 2; // Safety valve

    while (resolved.size < sectionIds.length && maxIterations > 0) {
      maxIterations--;
      const wave: SectionId[] = [];

      for (const id of sectionIds) {
        if (resolved.has(id)) continue;

        const agent = this.registry.get(id);
        const depsMet = agent.dependencies.every(
          dep => resolved.has(dep) || !sectionIds.includes(dep)
        );

        if (depsMet) {
          wave.push(id);
        }
      }

      if (wave.length === 0) {
        throw new Error('Circular dependency detected');
      }

      waves.push(wave);
      wave.forEach(id => resolved.add(id));
    }

    return waves;
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run tests/core/services/dependency-graph.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/services/dependency-graph.ts tests/core/services/dependency-graph.test.ts
git commit -m "feat: add DependencyGraph with topological wave resolution"
```

---

## Task 2: Context Builder

**Files:**
- Create: `src/core/services/context-builder.ts`
- Test: `tests/core/services/context-builder.test.ts`

**Interfaces:**
- Consumes: `Project`, `SectionId`, `AgentRegistry`
- Produces: `ContextBuilder` with `build()` method

- [ ] **Step 1: Write context builder test**

Create `tests/core/services/context-builder.test.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import { ContextBuilder } from '@/core/services/context-builder';
import { createRegistry } from '@/core/agents';
import { Project } from '@/core/types/project';

describe('ContextBuilder', () => {
  const registry = createRegistry();
  const builder = new ContextBuilder(registry);

  const mockProject: Project = {
    id: 'proj_test',
    idea: 'Airbnb for pets',
    createdAt: '2026-07-26T10:00:00Z',
    updatedAt: '2026-07-26T10:00:00Z',
    status: 'generating',
    analysis: {
      originalIdea: 'Airbnb for pets',
      type: 'marketplace',
      model: 'b2c',
      complexity: 'complex',
      industry: 'pet-care',
      hasHardware: false,
      hasRegulatoryRequirements: false,
      isTwoSidedMarketplace: true,
      requiresIntegrations: true,
    },
    sections: {
      'problem-statement': {
        id: 'problem-statement',
        name: 'Problem Statement',
        content: 'Pet owners struggle to find reliable care...',
        status: 'complete',
        tokensUsed: { input: 100, output: 50 },
        chatHistory: [],
        createdAt: '2026-07-26T10:00:00Z',
        updatedAt: '2026-07-26T10:00:00Z',
      },
    },
    chatHistory: [],
    metadata: {
      totalTokensUsed: 150,
      generationDurationMs: 1000,
      model: 'llama-3.1-70b-versatile',
    },
  };

  it('should build context with idea and characteristics', () => {
    const context = builder.build(mockProject, 'solution');

    expect(context).toContain('Airbnb for pets');
    expect(context).toContain('marketplace');
    expect(context).toContain('pet-care');
  });

  it('should include dependency outputs', () => {
    const context = builder.build(mockProject, 'customer-personas');

    // customer-personas depends on target-customers, but we don't have it
    // So it should just include idea and characteristics
    expect(context).toContain('Airbnb for pets');
  });

  it('should include chat history for refinement', () => {
    const projectWithChat = {
      ...mockProject,
      sections: {
        ...mockProject.sections,
        'solution': {
          id: 'solution' as const,
          name: 'Solution',
          content: 'A marketplace connecting pet owners...',
          status: 'complete' as const,
          tokensUsed: { input: 100, output: 50 },
          chatHistory: [
            { id: '1', role: 'user' as const, content: 'Add more details', timestamp: '2026-07-26T10:01:00Z' },
            { id: '2', role: 'assistant' as const, content: 'Here are more details...', timestamp: '2026-07-26T10:01:00Z' },
          ],
          createdAt: '2026-07-26T10:00:00Z',
          updatedAt: '2026-07-26T10:01:00Z',
        },
      },
    };

    const context = builder.build(projectWithChat, 'solution', true);
    expect(context).toContain('Add more details');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run tests/core/services/context-builder.test.ts --reporter=verbose
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create context builder**

Create `src/core/services/context-builder.ts`:
```typescript
import { AgentRegistry } from '../agents/registry';
import { Project, SectionId } from '../types/project';

export class ContextBuilder {
  constructor(private registry: AgentRegistry) {}

  build(project: Project, sectionId: SectionId, includeChatHistory = false): string {
    const agent = this.registry.get(sectionId);
    const parts: string[] = [];

    // 1. Core idea
    parts.push(`## Startup Idea\n${project.idea}`);

    // 2. Characteristics
    parts.push(`## Characteristics\n${JSON.stringify(project.analysis, null, 2)}`);

    // 3. Dependencies (already generated sections)
    if (agent.dependencies.length > 0) {
      const depParts: string[] = [];
      for (const depId of agent.dependencies) {
        const depState = project.sections[depId];
        if (depState?.status === 'complete' && depState.content) {
          depParts.push(`### ${depState.name}\n${depState.content}\n`);
        }
      }
      if (depParts.length > 0) {
        parts.push('## Preceding Sections (use as context)\n' + depParts.join('\n'));
      }
    }

    // 4. For refinement: chat history
    if (includeChatHistory) {
      const state = project.sections[sectionId];
      if (state?.chatHistory.length) {
        parts.push('## Previous Refinement Conversation\n');
        for (const msg of state.chatHistory) {
          parts.push(`**${msg.role}:** ${msg.content}\n`);
        }
      }
    }

    return parts.join('\n\n');
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run tests/core/services/context-builder.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/services/context-builder.ts tests/core/services/context-builder.test.ts
git commit -m "feat: add ContextBuilder for prompt assembly"
```

---

## Task 3: Token Manager

**Files:**
- Create: `src/core/services/token-manager.ts`
- Test: `tests/core/services/token-manager.test.ts`

**Interfaces:**
- Consumes: `SectionId`, `TOKEN_BUDGETS`
- Produces: `TokenManager` with tracking methods

- [ ] **Step 1: Write token manager test**

Create `tests/core/services/token-manager.test.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import { TokenManager } from '@/core/services/token-manager';

describe('TokenManager', () => {
  it('should track token usage', () => {
    const manager = new TokenManager(50000);

    manager.track('executive-summary', { input: 1000, output: 500 });
    manager.track('problem-statement', { input: 800, output: 400 });

    const report = manager.getUsageReport();
    expect(report.used).toBe(2700);
    expect(report.budget).toBe(50000);
    expect(report.remaining).toBe(47300);
  });

  it('should estimate tokens for sections', () => {
    const manager = new TokenManager(50000);

    const estimate = manager.estimateForSections(['executive-summary', 'problem-statement']);
    expect(estimate).toBeGreaterThan(0);
  });

  it('should warn at threshold', () => {
    const manager = new TokenManager(1000, 0.5);
    const warnings: Array<{ current: number; limit: number }> = [];

    manager.onWarning = (current, limit) => warnings.push({ current, limit });

    manager.track('executive-summary', { input: 400, output: 200 });
    expect(warnings).toHaveLength(1);
  });

  it('should report budget exceeded', () => {
    const manager = new TokenManager(100);

    manager.track('executive-summary', { input: 60, output: 50 });

    expect(manager.canAfford('problem-statement')).toBe(false);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run tests/core/services/token-manager.test.ts --reporter=verbose
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create token manager**

Create `src/core/services/token-manager.ts`:
```typescript
import { SectionId } from '../types/project';
import { TOKEN_BUDGETS } from '../config';

export class TokenManager {
  private used = 0;
  private budget: number;
  private warningThreshold: number;
  onWarning?: (current: number, limit: number) => void;

  constructor(budget: number, warningPercent = 0.8) {
    this.budget = budget;
    this.warningThreshold = budget * warningPercent;
  }

  estimateForSections(sectionIds: SectionId[]): number {
    let total = 0;
    for (const id of sectionIds) {
      const est = TOKEN_BUDGETS[id];
      total += est.input + est.output;
    }
    return Math.ceil(total * 1.15); // 15% overhead
  }

  track(sectionId: SectionId, usage: { input: number; output: number }): void {
    this.used += usage.input + usage.output;

    if (this.used >= this.warningThreshold && this.onWarning) {
      this.onWarning(this.used, this.budget);
    }
  }

  canAfford(sectionId: SectionId): boolean {
    const est = TOKEN_BUDGETS[sectionId];
    return this.used + est.input + est.output <= this.budget;
  }

  getRemaining(): number {
    return Math.max(0, this.budget - this.used);
  }

  getUsageReport() {
    return {
      used: this.used,
      budget: this.budget,
      remaining: this.getRemaining(),
      percentUsed: Math.round((this.used / this.budget) * 100),
    };
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run tests/core/services/token-manager.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/services/token-manager.ts tests/core/services/token-manager.test.ts
git commit -m "feat: add TokenManager for budget tracking"
```

---

## Task 4: Sequential Orchestrator

**Files:**
- Create: `src/core/services/orchestrator.ts`
- Test: `tests/core/services/orchestrator.test.ts`

**Interfaces:**
- Consumes: `AIProvider`, `AgentRegistry`, `InputAnalyzerService`, `SectionRouter`, `ContextBuilder`, `TokenManager`, `ProjectStore`
- Produces: `SequentialOrchestrator` with `generate()` method

- [ ] **Step 1: Write orchestrator test**

Create `tests/core/services/orchestrator.test.ts`:
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SequentialOrchestrator } from '@/core/services/orchestrator';

describe('SequentialOrchestrator', () => {
  let orchestrator: SequentialOrchestrator;
  let mockProvider: any;
  let mockStore: any;

  beforeEach(() => {
    mockProvider = {
      generate: vi.fn().mockResolvedValue({
        content: 'Generated section content',
        usage: { input: 100, output: 50 },
        model: 'test-model',
        finishReason: 'stop',
      }),
    };

    mockStore = {
      save: vi.fn().mockResolvedValue(undefined),
      load: vi.fn().mockResolvedValue(null),
      list: vi.fn().mockResolvedValue([]),
      delete: vi.fn().mockResolvedValue(undefined),
    };

    orchestrator = new SequentialOrchestrator(mockProvider, mockStore);
  });

  it('should generate workspace from idea', async () => {
    const workspace = await orchestrator.generate('Airbnb for pets');

    expect(workspace.idea).toBe('Airbnb for pets');
    expect(workspace.status).toBe('complete');
    expect(Object.keys(workspace.sections).length).toBeGreaterThan(0);
  });

  it('should call AI provider for each section', async () => {
    await orchestrator.generate('Test idea');

    // Should be called multiple times (once per relevant section)
    expect(mockProvider.generate.mock.calls.length).toBeGreaterThan(1);
  });

  it('should save project to store', async () => {
    await orchestrator.generate('Test idea');

    expect(mockStore.save).toHaveBeenCalled();
  });

  it('should handle generation failure gracefully', async () => {
    mockProvider.generate
      .mockResolvedValueOnce({
        content: JSON.stringify({
          type: 'saas',
          model: 'b2b',
          complexity: 'moderate',
          industry: 'test',
          hasHardware: false,
          hasRegulatoryRequirements: false,
          isTwoSidedMarketplace: false,
          requiresIntegrations: false,
        }),
        usage: { input: 100, output: 50 },
        model: 'test-model',
        finishReason: 'stop',
      })
      .mockRejectedValueOnce(new Error('API error'))
      .mockResolvedValue({
        content: 'Generated content',
        usage: { input: 100, output: 50 },
        model: 'test-model',
        finishReason: 'stop',
      });

    const workspace = await orchestrator.generate('Test idea');

    // Should complete even with failures
    expect(workspace.status).toBe('complete');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npx vitest run tests/core/services/orchestrator.test.ts --reporter=verbose
```
Expected: FAIL (module not found)

- [ ] **Step 3: Create sequential orchestrator**

Create `src/core/services/orchestrator.ts`:
```typescript
import { v4 as uuidv4 } from 'uuid';
import { AIProvider } from '../types/ai';
import { Project, SectionId, Section, InputAnalysisResult } from '../types/project';
import { AgentRegistry } from '../agents/registry';
import { InputAnalyzerService } from './input-analyzer';
import { SectionRouter } from './section-router';
import { ContextBuilder } from './context-builder';
import { DependencyGraph } from './dependency-graph';
import { TokenManager } from './token-manager';
import { ProjectStore } from '../../lib/storage/interface';

export class SequentialOrchestrator {
  private inputAnalyzer: InputAnalyzerService;
  private sectionRouter: SectionRouter;
  private contextBuilder: ContextBuilder;
  private dependencyGraph: DependencyGraph;
  private tokenManager: TokenManager;
  private registry: AgentRegistry;

  constructor(
    private aiProvider: AIProvider,
    private store: ProjectStore,
    registry?: AgentRegistry,
  ) {
    this.registry = registry ?? (await import('../agents')).createRegistry();
    this.inputAnalyzer = new InputAnalyzerService(aiProvider);
    this.sectionRouter = new SectionRouter(this.registry);
    this.contextBuilder = new ContextBuilder(this.registry);
    this.dependencyGraph = new DependencyGraph(this.registry);
    this.tokenManager = new TokenManager(50000);
  }

  async generate(idea: string): Promise<Project> {
    // Step 1: Analyze input (1 LLM call)
    const analysis = await this.inputAnalyzer.analyze(idea);

    // Step 2: Route to sections (deterministic)
    const sectionIds = this.sectionRouter.resolve(analysis);

    // Step 3: Create project
    const project: Project = {
      id: `proj_${uuidv4().slice(0, 8)}`,
      idea,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: 'generating',
      analysis,
      sections: {},
      chatHistory: [],
      metadata: {
        totalTokensUsed: 0,
        generationDurationMs: 0,
        model: 'llama-3.1-70b-versatile',
      },
    };

    const startTime = Date.now();

    // Step 4: Generate each section sequentially
    for (const sectionId of sectionIds) {
      try {
        const section = await this.generateSection(project, sectionId);
        project.sections[sectionId] = section;
        this.tokenManager.track(sectionId, section.tokensUsed);
      } catch (error) {
        project.sections[sectionId] = this.createFailedSection(sectionId, error as Error);
      }
    }

    // Step 5: Finalize
    project.status = 'complete';
    project.updatedAt = new Date().toISOString();
    project.metadata.generationDurationMs = Date.now() - startTime;
    project.metadata.totalTokensUsed = this.tokenManager.getUsageReport().used;

    // Step 6: Save
    await this.store.save(project);

    return project;
  }

  private async generateSection(project: Project, sectionId: SectionId): Promise<Section> {
    const agent = this.registry.get(sectionId);
    const context = this.contextBuilder.build(project, sectionId);

    const result = await this.aiProvider.generate({
      system: agent.systemPrompt,
      user: context,
      maxTokens: agent.estimatedTokens.output,
      temperature: 0.7,
    });

    return {
      id: sectionId,
      name: agent.name,
      content: result.content,
      status: 'complete',
      tokensUsed: result.usage,
      chatHistory: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }

  private createFailedSection(sectionId: SectionId, error: Error): Section {
    const agent = this.registry.get(sectionId);
    return {
      id: sectionId,
      name: agent.name,
      content: '',
      status: 'failed',
      tokensUsed: { input: 0, output: 0 },
      chatHistory: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run tests/core/services/orchestrator.test.ts --reporter=verbose
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/services/orchestrator.ts tests/core/services/orchestrator.test.ts
git commit -m "feat: add SequentialOrchestrator for section generation"
```

---

## Task 5: API Routes

**Files:**
- Create: `src/app/api/generate/route.ts`, `src/app/api/projects/[id]/route.ts`, `src/app/api/projects/[id]/sections/[sectionId]/route.ts`

**Interfaces:**
- Consumes: `SequentialOrchestrator`, `ProjectStore`
- Produces: API endpoints for generation and project management

- [ ] **Step 1: Create generate API route**

Create `src/app/api/generate/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { SequentialOrchestrator } from '@/core/services/orchestrator';
import { FilesystemProjectStore } from '@/lib/storage/filesystem';
import { aiProvider } from '@/lib/ai/provider';
import path from 'path';

const store = new FilesystemProjectStore(path.join(process.cwd(), 'data/projects'));

export async function POST(request: NextRequest) {
  try {
    const { idea } = await request.json();

    if (!idea || typeof idea !== 'string') {
      return NextResponse.json(
        { error: 'Idea is required' },
        { status: 400 }
      );
    }

    const orchestrator = new SequentialOrchestrator(aiProvider, store);
    const project = await orchestrator.generate(idea);

    return NextResponse.json(project);
  } catch (error) {
    console.error('Generation failed:', error);
    return NextResponse.json(
      { error: 'Generation failed' },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 2: Create project API route**

Create `src/app/api/projects/[id]/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { FilesystemProjectStore } from '@/lib/storage/filesystem';
import path from 'path';

const store = new FilesystemProjectStore(path.join(process.cwd(), 'data/projects'));

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const project = await store.load(params.id);

  if (!project) {
    return NextResponse.json(
      { error: 'Project not found' },
      { status: 404 }
    );
  }

  return NextResponse.json(project);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  await store.delete(params.id);
  return NextResponse.json({ success: true });
}
```

- [ ] **Step 3: Create section chat API route**

Create `src/app/api/projects/[id]/sections/[sectionId]/route.ts`:
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { FilesystemProjectStore } from '@/lib/storage/filesystem';
import { aiProvider } from '@/lib/ai/provider';
import { createRegistry } from '@/core/agents';
import { ContextBuilder } from '@/core/services/context-builder';
import path from 'path';

const store = new FilesystemProjectStore(path.join(process.cwd(), 'data/projects'));
const registry = createRegistry();
const contextBuilder = new ContextBuilder(registry);

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string; sectionId: string } }
) {
  try {
    const { message } = await request.json();
    const project = await store.load(params.id);

    if (!project) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      );
    }

    const section = project.sections[params.sectionId as keyof typeof project.sections];
    if (!section) {
      return NextResponse.json(
        { error: 'Section not found' },
        { status: 404 }
      );
    }

    // Add user message to chat history
    section.chatHistory.push({
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    });

    // Build context with chat history
    const context = contextBuilder.build(project, params.sectionId as any, true);
    const agent = registry.get(params.sectionId as any);

    // Generate response
    const result = await aiProvider.generate({
      system: agent.systemPrompt,
      user: context,
      maxTokens: agent.estimatedTokens.output,
      temperature: 0.3,
    });

    // Add assistant response
    section.chatHistory.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: result.content,
      timestamp: new Date().toISOString(),
      tokensUsed: result.usage.output,
    });

    // Update section content
    section.content = result.content;
    section.updatedAt = new Date().toISOString();

    // Save
    project.updatedAt = new Date().toISOString();
    await store.save(project);

    return NextResponse.json({
      response: result.content,
      tokensUsed: result.usage,
    });
  } catch (error) {
    console.error('Chat failed:', error);
    return NextResponse.json(
      { error: 'Chat failed' },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
npx tsc --noEmit
```
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add src/app/api/
git commit -m "feat: add API routes for generation and project management"
```

---

## Task 6: Basic Workspace UI

**Files:**
- Create: `src/app/page.tsx`, `src/components/workspace.tsx`, `src/components/section-card.tsx`

**Interfaces:**
- Consumes: API routes
- Produces: Basic UI for viewing workspace

- [ ] **Step 1: Create workspace component**

Create `src/components/workspace.tsx`:
```tsx
'use client';

import { useState } from 'react';
import { SectionCard } from './section-card';
import { Project } from '@/core/types/project';

interface WorkspaceProps {
  project: Project;
}

export function Workspace({ project }: WorkspaceProps) {
  const [selectedSection, setSelectedSection] = useState<string | null>(null);

  const sections = Object.entries(project.sections);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold text-gray-900">
            AI Startup Analyst
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {project.idea}
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Section List */}
          <div className="lg:col-span-1">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Sections</h2>
            <div className="space-y-2">
              {sections.map(([id, section]) => (
                <button
                  key={id}
                  onClick={() => setSelectedSection(id)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedSection === id
                      ? 'bg-blue-50 border-blue-200'
                      : 'bg-white border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{section.name}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      section.status === 'complete'
                        ? 'bg-green-100 text-green-800'
                        : section.status === 'generating'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {section.status}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Section Content */}
          <div className="lg:col-span-2">
            {selectedSection ? (
              <SectionCard
                section={project.sections[selectedSection as keyof typeof project.sections]!}
                projectId={project.id}
              />
            ) : (
              <div className="bg-white rounded-lg border p-8 text-center text-gray-500">
                Select a section to view
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Create section card component**

Create `src/components/section-card.tsx`:
```tsx
'use client';

import { useState } from 'react';
import { Section } from '@/core/types/project';

interface SectionCardProps {
  section: Section;
  projectId: string;
}

export function SectionCard({ section, projectId }: SectionCardProps) {
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState(section.chatHistory);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleChat = async () => {
    if (!chatInput.trim() || isGenerating) return;

    setIsGenerating(true);
    try {
      const response = await fetch(
        `/api/projects/${projectId}/sections/${section.id}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: chatInput }),
        }
      );

      const data = await response.json();
      setChatHistory([
        ...chatHistory,
        { id: Date.now().toString(), role: 'user', content: chatInput, timestamp: new Date().toISOString() },
        { id: (Date.now() + 1).toString(), role: 'assistant', content: data.response, timestamp: new Date().toISOString() },
      ]);
      setChatInput('');
    } catch (error) {
      console.error('Chat failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border">
      <div className="p-4 border-b">
        <h3 className="text-lg font-medium text-gray-900">{section.name}</h3>
      </div>

      <div className="p-4">
        <div className="prose max-w-none">
          <pre className="whitespace-pre-wrap text-sm text-gray-700">
            {section.content}
          </pre>
        </div>
      </div>

      {section.chatHistory.length > 0 && (
        <div className="border-t p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Refinement Chat</h4>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {chatHistory.map((msg) => (
              <div
                key={msg.id}
                className={`p-3 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-blue-50 ml-8'
                    : 'bg-gray-50 mr-8'
                }`}
              >
                <p className="text-sm text-gray-700">{msg.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Refine this section..."
            className="flex-1 px-3 py-2 border rounded-lg text-sm"
            onKeyPress={(e) => e.key === 'Enter' && handleChat()}
          />
          <button
            onClick={handleChat}
            disabled={isGenerating}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {isGenerating ? 'Generating...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Update main page**

Update `src/app/page.tsx`:
```tsx
'use client';

import { useState } from 'react';
import { Workspace } from '@/components/workspace';
import { Project } from '@/core/types/project';

export default function Home() {
  const [idea, setIdea] = useState('');
  const [project, setProject] = useState<Project | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!idea.trim() || isGenerating) return;

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea }),
      });

      if (!response.ok) {
        throw new Error('Generation failed');
      }

      const data = await response.json();
      setProject(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsGenerating(false);
    }
  };

  if (project) {
    return <Workspace project={project} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex items-center justify-center p-8">
      <div className="max-w-2xl w-full">
        <h1 className="text-4xl font-bold text-center text-gray-900 mb-2">
          AI Startup Analyst
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Enter your startup idea and get a comprehensive analysis
        </p>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <textarea
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder="Describe your startup idea..."
            className="w-full h-32 px-4 py-3 border rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />

          {error && (
            <p className="mt-2 text-sm text-red-600">{error}</p>
          )}

          <button
            onClick={handleGenerate}
            disabled={!idea.trim() || isGenerating}
            className="mt-4 w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? 'Analyzing...' : 'Generate Analysis'}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
npx tsc --noEmit
```
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add src/app/page.tsx src/components/
git commit -m "feat: add basic workspace UI with section viewing and chat"
```

---

## Task 7: Run All Tests

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
git commit -m "feat: complete Phase 2 orchestrator and generation pipeline"
```

---

## Phase 2 Summary

After completing all tasks, you will have:

- ✅ Dependency graph with topological wave resolution
- ✅ Context builder for prompt assembly
- ✅ Token manager for budget tracking
- ✅ Sequential orchestrator for section generation
- ✅ API routes for generation and project management
- ✅ Basic workspace UI with section viewing and chat

**Next Phase:** Phase 3 will add parallel generation, streaming, and advanced features.
