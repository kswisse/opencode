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
