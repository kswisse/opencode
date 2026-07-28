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

  it('should not throw on valid dependencies', () => {
    const circularIds = ['revenue-model', 'pricing-strategy', 'financial-assumptions'];
    const waves = graph.topologicalWaves(circularIds);
    expect(waves.length).toBeGreaterThan(0);
  });
});
