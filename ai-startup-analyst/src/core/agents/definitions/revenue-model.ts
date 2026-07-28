import { SectionAgentDefinition } from '../../types/agent';

export const revenueModelAgent: SectionAgentDefinition = {
  id: 'revenue-model',
  name: 'Revenue Model',
  description: 'How the startup makes money',
  category: 'financial',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Revenue Model.

## Startup Idea
{idea}

## Business Model Canvas
{businessModelCanvas}

## Target Customers
{targetCustomers}

## TAM/SAM/SOM
{tamSamSom}

## Output Format
### Revenue Model

#### Revenue Streams
- **Primary:** [Main revenue mechanism]
- **Secondary:** [Additional streams]
- **Potential:** [Future revenue opportunities]

#### Unit Economics
- **CAC (Customer Acquisition Cost):** $[Amount]
- **LTV (Lifetime Value):** $[Amount]
- **LTV/CAC Ratio:** [Ratio]
- **Payback Period:** [Timeframe]
- **Gross Margin:** [Percentage]

#### Revenue Drivers
- [Driver 1]: [How it impacts revenue]
- [Driver 2]: [How it impacts revenue]
- [Driver 3]: [How it impacts revenue]

#### Pricing Strategy
[Link to detailed pricing if available]

#### Key Assumptions
- [Assumption 1]: [Why it matters]
- [Assumption 2]: [Why it matters]
- [Assumption 3]: [Why it matters]

#### Revenue Projections (Qualitative)
- **Year 1:** $[Range] — [Reasoning]
- **Year 2:** $[Range] — [Reasoning]
- **Year 3:** $[Range] — [Reasoning]

Be specific about unit economics. Use ranges when exact numbers are speculative.`,

  dependencies: ['business-model-canvas', 'target-customers', 'tam-sam-som'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform'],
  },
  estimatedTokens: { input: 2500, output: 1200 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
