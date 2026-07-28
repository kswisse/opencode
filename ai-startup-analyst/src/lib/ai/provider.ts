import { AIProvider, GenerateParams, GenerateResult } from '@/core/types/ai';
import { GroqProvider } from './groq';
import { GeminiProvider } from './gemini';

export class AIProviderChain implements AIProvider {
  private providers: AIProvider[];

  constructor(providers?: AIProvider[]) {
    this.providers = providers ?? [new GroqProvider(), new GeminiProvider()];
  }

  async generate(params: GenerateParams): Promise<GenerateResult> {
    let lastError: Error | undefined;

    for (const provider of this.providers) {
      try {
        return await provider.generate(params);
      } catch (error) {
        lastError = error as Error;
        console.warn(`Provider ${provider.constructor.name} failed: ${lastError.message}`);
      }
    }

    throw new Error(`All AI providers failed: ${lastError?.message}`);
  }
}

export const aiProvider = new AIProviderChain();
