import { SectionId, InputAnalysisResult } from './project';

export interface SectionAgentDefinition {
  id: SectionId;
  name: string;
  description: string;
  category: 'strategy' | 'market' | 'financial' | 'technical' | 'operational';
  systemPrompt: string;
  dependencies: SectionId[];
  relevantFor: {
    types?: string[];
    models?: string[];
    complexity?: string[];
    flags?: Array<keyof Pick<InputAnalysisResult,
      'hasHardware' | 'hasRegulatoryRequirements' | 'isTwoSidedMarketplace' | 'requiresIntegrations'>>;
  };
  estimatedTokens: { input: number; output: number };
  outputFormat: 'markdown' | 'json' | 'structured-markdown';
  chatEnabled: boolean;
  maxRetries: number;
  timeoutSeconds: number;
}

export interface SectionAgentState {
  definition: SectionAgentDefinition;
  status: 'pending' | 'generating' | 'completed' | 'failed' | 'skipped';
  result?: string;
  error?: string;
  attempts: number;
  startedAt?: Date;
  completedAt?: Date;
  tokensUsed: { input: number; output: number };
}
