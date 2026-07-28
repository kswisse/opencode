import { describe, it, expect, vi, beforeEach } from 'vitest';
import { InputAnalyzerService } from '@/core/services/input-analyzer';

describe('InputAnalyzerService', () => {
  let analyzer: InputAnalyzerService;
  let mockProvider: any;

  beforeEach(() => {
    mockProvider = {
      generate: vi.fn().mockResolvedValue({
        content: JSON.stringify({
          type: 'marketplace',
          model: 'b2c',
          complexity: 'complex',
          industry: 'pet-care',
          hasHardware: false,
          hasRegulatoryRequirements: false,
          isTwoSidedMarketplace: true,
          requiresIntegrations: true,
        }),
        usage: { input: 100, output: 50 },
        model: 'test-model',
        finishReason: 'stop',
      }),
    };

    analyzer = new InputAnalyzerService(mockProvider);
  });

  it('should analyze a startup idea', async () => {
    const result = await analyzer.analyze('I want to build Airbnb for pets');

    expect(result.originalIdea).toBe('I want to build Airbnb for pets');
    expect(result.type).toBe('marketplace');
    expect(result.model).toBe('b2c');
    expect(result.isTwoSidedMarketplace).toBe(true);
  });

  it('should call AI provider with correct params', async () => {
    await analyzer.analyze('Test idea');

    expect(mockProvider.generate).toHaveBeenCalledWith(
      expect.objectContaining({
        maxTokens: 500,
        temperature: 0.1,
      })
    );
  });

  it('should handle invalid JSON response', async () => {
    mockProvider.generate.mockResolvedValue({
      content: 'Invalid JSON',
      usage: { input: 100, output: 50 },
      model: 'test-model',
      finishReason: 'stop',
    });

    await expect(analyzer.analyze('Test idea')).rejects.toThrow();
  });
});
