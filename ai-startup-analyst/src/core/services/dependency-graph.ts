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
