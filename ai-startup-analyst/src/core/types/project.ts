export type SectionId =
  | 'executive-summary'
  | 'problem-statement'
  | 'solution'
  | 'target-customers'
  | 'customer-personas'
  | 'tam-sam-som'
  | 'competitor-analysis'
  | 'swot-analysis'
  | 'business-model-canvas'
  | 'revenue-model'
  | 'pricing-strategy'
  | 'go-to-market-strategy'
  | 'mvp-definition'
  | 'feature-prioritization'
  | 'technical-architecture'
  | 'suggested-tech-stack'
  | 'database-design'
  | 'api-overview'
  | 'ui-sitemap'
  | 'product-roadmap'
  | 'risk-analysis'
  | 'financial-assumptions'
  | 'launch-checklist';

export const ALL_SECTION_IDS: SectionId[] = [
  'executive-summary', 'problem-statement', 'solution',
  'target-customers', 'customer-personas', 'tam-sam-som',
  'competitor-analysis', 'swot-analysis', 'business-model-canvas',
  'revenue-model', 'pricing-strategy', 'go-to-market-strategy',
  'mvp-definition', 'feature-prioritization', 'technical-architecture',
  'suggested-tech-stack', 'database-design', 'api-overview',
  'ui-sitemap', 'product-roadmap', 'risk-analysis',
  'financial-assumptions', 'launch-checklist',
];

export interface InputAnalysisResult {
  originalIdea: string;
  type: 'marketplace' | 'saas' | 'e-commerce' | 'fintech' | 'healthtech'
    | 'edtech' | 'social' | 'hardware' | 'platform' | 'api' | 'agency' | 'other';
  model: 'b2b' | 'b2c' | 'b2b2c' | 'd2c' | 'marketplace' | 'hybrid';
  complexity: 'simple' | 'moderate' | 'complex' | 'highly-complex';
  industry: string;
  hasHardware: boolean;
  hasRegulatoryRequirements: boolean;
  isTwoSidedMarketplace: boolean;
  requiresIntegrations: boolean;
}

export interface Section {
  id: SectionId;
  name: string;
  content: string;
  status: 'pending' | 'generating' | 'complete' | 'failed';
  tokensUsed: { input: number; output: number };
  chatHistory: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tokensUsed?: number;
}

export interface Project {
  id: string;
  idea: string;
  createdAt: string;
  updatedAt: string;
  status: 'analyzing' | 'generating' | 'complete' | 'error';
  analysis: InputAnalysisResult;
  sections: Partial<Record<SectionId, Section>>;
  chatHistory: ChatMessage[];
  metadata: {
    totalTokensUsed: number;
    generationDurationMs: number;
    model: string;
  };
}

export interface ProjectSummary {
  id: string;
  idea: string;
  createdAt: string;
  updatedAt: string;
  sectionCount: number;
  totalTokens: number;
}
