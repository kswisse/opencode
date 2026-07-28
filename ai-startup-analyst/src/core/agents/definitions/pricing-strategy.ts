import { SectionAgentDefinition } from '../../types/agent';

export const pricingStrategyAgent: SectionAgentDefinition = {
  id: 'pricing-strategy',
  name: 'Pricing Strategy',
  description: 'Pricing model and tiers',
  category: 'financial',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Pricing Strategy.

## Startup Idea
{idea}

## Revenue Model
{revenueModel}

## Competitor Analysis
{competitorAnalysis}

## Output Format
### Pricing Strategy

#### Pricing Model
[Description of pricing approach - freemium, subscription, usage-based, etc.]

#### Pricing Tiers
| Tier | Price | Features | Target Segment |
|------|-------|----------|----------------|
| [Free/Basic] | $0 | [Features] | [Who] |
| [Pro] | $[Price]/mo | [Features] | [Who] |
| [Enterprise] | Custom | [Features] | [Who] |

#### Competitive Pricing Analysis
| Competitor | Their Price | Our Price | Differentiation |
|-----------|-------------|-----------|-----------------|
| [Name] | $[Price] | $[Price] | [Why different] |

#### Pricing Rationale
- **Value-Based:** [How pricing reflects value delivered]
- **Cost-Based:** [How pricing covers costs]
- **Market-Based:** [How pricing compares to market]

#### Conversion Strategy
- **Free → Paid:** [How to convert free users]
- **Upsell Paths:** [How to move users to higher tiers]
- **Retention:** [How to keep paying customers]

#### Revenue Projections by Tier
- [Tier 1]: $[Amount]/month at [X] customers
- [Tier 2]: $[Amount]/month at [X] customers
- [Tier 3]: $[Amount]/month at [X] customers

Justify pricing decisions with market research and value analysis.`,

  dependencies: ['revenue-model', 'competitor-analysis'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform'],
  },
  estimatedTokens: { input: 2500, output: 1000 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 45,
};
