import { v4 as uuidv4 } from 'uuid';
import { AIProvider } from '../types/ai';
import { Project, SectionId, Section } from '../types/project';
import { AgentRegistry } from '../agents/registry';
import { createRegistry } from '../agents';
import { InputAnalyzerService } from './input-analyzer';
import { SectionRouter } from './section-router';
import { ContextBuilder } from './context-builder';
import { TokenManager } from './token-manager';
import { ProjectStore } from '../../lib/storage/interface';

export class SequentialOrchestrator {
  private inputAnalyzer: InputAnalyzerService;
  private sectionRouter: SectionRouter;
  private contextBuilder: ContextBuilder;
  private tokenManager: TokenManager;
  private registry: AgentRegistry;

  constructor(
    private aiProvider: AIProvider,
    private store: ProjectStore,
    registry?: AgentRegistry,
  ) {
    this.registry = registry ?? createRegistry();
    this.inputAnalyzer = new InputAnalyzerService(aiProvider);
    this.sectionRouter = new SectionRouter(this.registry);
    this.contextBuilder = new ContextBuilder(this.registry);
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
