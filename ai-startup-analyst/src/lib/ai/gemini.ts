import { AIProvider, GenerateParams, GenerateResult } from '@/core/types/ai';

export class GeminiProvider implements AIProvider {
  private model = 'gemini-1.5-flash';

  async generate(params: GenerateParams): Promise<GenerateResult> {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) throw new Error('GEMINI_API_KEY is required');

    const url = `https://generativelanguage.googleapis.com/v1beta/models/${this.model}:generateContent?key=${apiKey}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: `${params.system}\n\n${params.user}` }] }],
        generationConfig: {
          maxOutputTokens: params.maxTokens,
          temperature: params.temperature ?? 0.7,
        },
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Gemini API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    const content = data.candidates[0].content.parts[0].text;

    return {
      content,
      usage: {
        input: data.usageMetadata?.promptTokenCount ?? 0,
        output: data.usageMetadata?.candidatesTokenCount ?? 0,
      },
      model: this.model,
      finishReason: 'stop',
    };
  }
}
