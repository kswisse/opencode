import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AIProviderChain } from '@/lib/ai/provider';

describe('AIProviderChain', () => {
  beforeEach(() => {
    vi.stubEnv('GROQ_API_KEY', 'test-groq-key');
    vi.stubEnv('GEMINI_API_KEY', 'test-gemini-key');
  });

  it('should try providers in order', async () => {
    const mockProvider1 = {
      generate: vi.fn().mockRejectedValue(new Error('Provider 1 failed')),
    };
    const mockProvider2 = {
      generate: vi.fn().mockResolvedValue({
        content: 'Test response',
        usage: { input: 100, output: 50 },
        model: 'test-model',
        finishReason: 'stop',
      }),
    };

    const chain = new AIProviderChain([mockProvider1 as any, mockProvider2 as any]);
    const result = await chain.generate({
      system: 'Test system',
      user: 'Test user',
      maxTokens: 100,
    });

    expect(mockProvider1.generate).toHaveBeenCalledOnce();
    expect(mockProvider2.generate).toHaveBeenCalledOnce();
    expect(result.content).toBe('Test response');
  });

  it('should throw when all providers fail', async () => {
    const mockProvider = {
      generate: vi.fn().mockRejectedValue(new Error('Provider failed')),
    };

    const chain = new AIProviderChain([mockProvider as any]);
    await expect(chain.generate({
      system: 'Test system',
      user: 'Test user',
      maxTokens: 100,
    })).rejects.toThrow('All AI providers failed');
  });
});
