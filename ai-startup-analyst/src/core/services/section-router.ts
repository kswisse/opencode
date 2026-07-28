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

  private isRelevant(
    agent: { relevantFor: Record<string, any> },
    analysis: InputAnalysisResult
  ): boolean {
    const { relevantFor } = agent;

    // Empty relevantFor = always relevant
    if (!relevantFor.types?.length && !relevantFor.models?.length && !relevantFor.complexity?.length && !relevantFor.flags?.length) {
      return true;
    }

    // If complexity is specified, it must match (AND logic)
    if (relevantFor.complexity?.length && !relevantFor.complexity.includes(analysis.complexity)) {
      return false;
    }

    // For other conditions, use OR logic
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

    // If no OR conditions matched but complexity matched, still relevant
    if (!match && relevantFor.complexity?.length) {
      return true;
    }

    return match;
  }
}
