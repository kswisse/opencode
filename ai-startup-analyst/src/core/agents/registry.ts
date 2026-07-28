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
