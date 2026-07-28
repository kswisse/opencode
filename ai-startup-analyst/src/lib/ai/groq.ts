import { AIProvider, GenerateParams, GenerateResult } from '@/core/types/ai';

export class GroqProvider implements AIProvider {
  private model = 'llama-3.1-70b-versatile';

  async generate(params: GenerateParams): Promise<GenerateResult> {
    const apiKey = process.env.GROQ_API_KEY;
    if (!apiKey) throw new Error('GROQ_API_KEY is required');

    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: this.model,
        messages: [
          { role: 'system', content: params.system },
          { role: 'user', content: params.user },
        ],
        max_tokens: params.maxTokens,
        temperature: params.temperature ?? 0.7,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Groq API error: ${response.status} - ${error}`);
    }

    const data = await response.json();
    const choice = data.choices[0];

    return {
      content: choice.message.content,
      usage: {
        input: data.usage.prompt_tokens,
        output: data.usage.completion_tokens,
      },
      model: data.model,
      finishReason: choice.finish_reason === 'stop' ? 'stop' : 'length',
    };
  }
}
