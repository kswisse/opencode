export interface GenerateParams {
  system: string;
  user: string;
  maxTokens: number;
  temperature?: number;
  timeout?: number;
}

export interface GenerateResult {
  content: string;
  usage: { input: number; output: number };
  model: string;
  finishReason: 'stop' | 'length' | 'timeout' | 'error';
}

export interface AIProvider {
  generate(params: GenerateParams): Promise<GenerateResult>;
}
