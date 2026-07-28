import { AIProvider } from '@/core/types/ai';
import { InputAnalysisResult } from '@/core/types/project';

export class InputAnalyzerService {
  private systemPrompt = `Analyze this startup idea and output JSON with:
- type: marketplace|saas|e-commerce|fintech|healthtech|edtech|social|hardware|platform|api|agency|other
- model: b2b|b2c|b2b2c|d2c|marketplace|hybrid
- complexity: simple|moderate|complex|highly-complex
- industry: specific industry string (e.g., "pet-care", "fintech", "healthcare")
- hasHardware: boolean — does this involve physical hardware?
- hasRegulatoryRequirements: boolean — is this a regulated industry?
- isTwoSidedMarketplace: boolean — are there two distinct user groups?
- requiresIntegrations: boolean — does this need third-party APIs/services?
Output ONLY valid JSON. No explanation.`;

  constructor(private aiProvider: AIProvider) {}

  async analyze(idea: string): Promise<InputAnalysisResult> {
    const response = await this.aiProvider.generate({
      system: this.systemPrompt,
      user: idea,
      maxTokens: 500,
      temperature: 0.1,
    });

    return {
      originalIdea: idea,
      ...JSON.parse(response.content),
    };
  }
}
