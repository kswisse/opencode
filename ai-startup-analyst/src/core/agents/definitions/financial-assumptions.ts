import { SectionAgentDefinition } from '../../types/agent';

export const financialAssumptionsAgent: SectionAgentDefinition = {
  id: 'financial-assumptions',
  name: 'Financial Assumptions',
  description: 'Key financial assumptions and projections',
  category: 'financial',

  systemPrompt: `You are a senior financial analyst. Generate comprehensive Financial Assumptions.

## Startup Idea
{idea}

## Revenue Model
{revenueModel}

## Pricing Strategy
{pricingStrategy}

## Business Model Canvas
{businessModelCanvas}

## Output Format
### Financial Assumptions

#### Key Assumptions
| Assumption | Value | Source/Reasoning |
|-----------|-------|------------------|
| [Assumption 1] | [Value] | [Why] |
| [Assumption 2] | [Value] | [Why] |
| [Assumption 3] | [Value] | [Why] |

#### Revenue Projections
| Year | Users | ARPU | Revenue | Growth |
|------|-------|------|---------|--------|
| Year 1 | [Number] | $[Amount] | $[Amount] | - |
| Year 2 | [Number] | $[Amount] | $[Amount] | [%] |
| Year 3 | [Number] | $[Amount] | $[Amount] | [%] |

#### Cost Projections
| Category | Year 1 | Year 2 | Year 3 |
|----------|--------|--------|--------|
| Hosting | $[Amount] | $[Amount] | $[Amount] |
| Marketing | $[Amount] | $[Amount] | $[Amount] |
| Team | $[Amount] | $[Amount] | $[Amount] |
| Operations | $[Amount] | $[Amount] | $[Amount] |
| **Total** | $[Amount] | $[Amount] | $[Amount] |

#### Key Metrics
| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| MRR | $[Amount] | $[Amount] | $[Amount] |
| ARR | $[Amount] | $[Amount] | $[Amount] |
| Burn Rate | $[Amount]/mo | $[Amount]/mo | $[Amount]/mo |
| Runway | [Months] | [Months] | [Months] |

#### Break-Even Analysis
- **Monthly Costs:** $[Amount]
- **Revenue Needed:** $[Amount]
- **Users Needed:** [Number]
- **Timeline to Break-Even:** [Timeframe]

#### Sensitivity Analysis
- **Best Case:** [Description]
- **Base Case:** [Description]
- **Worst Case:** [Description]

#### Funding Requirements
- **Pre-Seed:** $[Amount] — [What it funds]
- **Seed:** $[Amount] — [What it funds]
- **Series A:** $[Amount] — [What it funds]

Be conservative in projections. Always explain your assumptions.`,

  dependencies: ['revenue-model', 'pricing-strategy', 'business-model-canvas'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform'],
  },
  estimatedTokens: { input: 3000, output: 1500 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
