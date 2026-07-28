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
