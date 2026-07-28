import { SectionAgentDefinition } from '../../types/agent';

export const tamSamSomAgent: SectionAgentDefinition = {
  id: 'tam-sam-som',
  name: 'TAM / SAM / SOM',
  description: 'Market sizing analysis',
  category: 'market',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive TAM/SAM/SOM analysis.

## Startup Idea
{idea}

## Target Customers
{targetCustomers}

## Output Format
### TAM / SAM / SOM

#### Total Addressable Market (TAM)
- **Definition:** [What TAM represents for this market]
- **Size:** $[Amount] [B/M/K]
- **Methodology:** [How you calculated it]
- **Source:** [Data source or estimation method]

#### Serviceable Addressable Market (SAM)
- **Definition:** [What SAM represents - the segment you can serve]
- **Size:** $[Amount] [B/M/K]
- **Methodology:** [How you calculated it]
- **Rationale:** [Why this portion is serviceable]

#### Serviceable Obtainable Market (SOM)
- **Definition:** [What SOM represents - what you can realistically capture]
- **Size:** $[Amount] [B/M/K]
- **Methodology:** [How you calculated it]
- **Assumptions:** [Key assumptions made]

#### Market Visualization
- **TAM:** $[Amount] [B/M/K] (Total market)
- **SAM:** $[Amount] [B/M/K] (Serviceable segment)
- **SOM:** $[Amount] [B/M/K] (Obtainable share)

#### Growth Projections
- Year 1: $[Amount]
- Year 3: $[Amount]
- Year 5: $[Amount]

Use reasonable estimates. Always explain your methodology and assumptions.`,

  dependencies: ['target-customers'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform'],
  },
  estimatedTokens: { input: 2000, output: 1200 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 45,
};
