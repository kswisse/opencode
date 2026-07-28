import { SectionAgentDefinition } from '../../types/agent';

export const featurePrioritizationAgent: SectionAgentDefinition = {
  id: 'feature-prioritization',
  name: 'Feature Prioritization',
  description: 'Feature ranking and prioritization',
  category: 'operational',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Feature Prioritization.

## Startup Idea
{idea}

## Solution
{solution}

## Customer Personas
{customerPersonas}

## Competitor Analysis
{competitorAnalysis}

## Output Format
### Feature Prioritization

#### Feature List
| Feature | Impact | Effort | Priority | Phase |
|---------|--------|--------|----------|-------|
| [Feature 1] | [High/Med/Low] | [High/Med/Low] | [P1/P2/P3] | [MVP/V2/V3] |
| [Feature 2] | [High/Med/Low] | [High/Med/Low] | [P1/P2/P3] | [MVP/V2/V3] |

#### Impact vs Effort Matrix
- **Quick Wins (High Impact, Low Effort):** [Features]
- **Major Projects (High Impact, High Effort):** [Features]
- **Fill-Ins (Low Impact, Low Effort):** [Features]
- **Avoid (Low Impact, High Effort):** [Features]

#### P0 Features (Must Have for MVP)
1. [Feature]: [Why it's critical]
2. [Feature]: [Why it's critical]

#### P1 Features (Important, V2)
1. [Feature]: [Why it matters]
2. [Feature]: [Why it matters]

#### P2 Features (Nice to Have, V3+)
1. [Feature]: [When to build]
2. [Feature]: [When to build]

#### Rationale
[Why this prioritization makes sense for the startup's stage and goals]

Prioritize based on user value, business impact, and technical feasibility.`,

  dependencies: ['solution', 'customer-personas', 'competitor-analysis'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform'],
  },
  estimatedTokens: { input: 2500, output: 1200 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
