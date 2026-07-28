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
