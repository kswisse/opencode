import { SectionAgentDefinition } from '../../types/agent';

export const competitorAnalysisAgent: SectionAgentDefinition = {
  id: 'competitor-analysis',
  name: 'Competitor Analysis',
  description: 'Analysis of existing competitors',
  category: 'market',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Competitor Analysis.

## Startup Idea
{idea}

## Target Customers
{targetCustomers}

## Output Format
### Competitor Analysis

#### Direct Competitors
| Competitor | Description | Strengths | Weaknesses | Funding |
|-----------|-------------|-----------|------------|---------|
| [Name] | [What they do] | [Key strengths] | [Key weaknesses] | [Funding stage] |

#### Indirect Competitors
| Competitor | Description | Threat Level | Why |
|-----------|-------------|--------------|-----|
| [Name] | [What they do] | [High/Med/Low] | [Why they're a threat] |

#### Competitive Landscape
[Chart or visualization of competitive positioning]

#### Competitive Advantages
1. **[Advantage 1]:** [Description]
2. **[Advantage 2]:** [Description]
3. **[Advantage 3]:** [Description]

#### Market Gaps
- [Gap 1]: [Unmet need in the market]
- [Gap 2]: [Opportunity no one is addressing]

#### Competitive Moats
[How to build defensibility over time]

Research real competitors when possible. Be specific about strengths and weaknesses.`,

  dependencies: ['target-customers'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform'],
  },
  estimatedTokens: { input: 2500, output: 1500 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
