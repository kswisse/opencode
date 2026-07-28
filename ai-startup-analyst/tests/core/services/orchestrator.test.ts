import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SequentialOrchestrator } from '@/core/services/orchestrator';

describe('SequentialOrchestrator', () => {
  let orchestrator: SequentialOrchestrator;
  let mockProvider: any;
  let mockStore: any;

  beforeEach(() => {
    mockProvider = {
      generate: vi.fn().mockResolvedValue({
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
    const project = await orchestrator.generate('Airbnb for pets');

    expect(project.idea).toBe('Airbnb for pets');
    expect(project.status).toBe('complete');
    expect(Object.keys(project.sections).length).toBeGreaterThan(0);
  });

  it('should call AI provider for each section', async () => {
    await orchestrator.generate('Test idea');

    // Should be called multiple times (once for input analysis + once per relevant section)
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

    const project = await orchestrator.generate('Test idea');

    // Should complete even with failures
    expect(project.status).toBe('complete');
  });
});
