import { SectionAgentDefinition } from '../../types/agent';

export const customerPersonasAgent: SectionAgentDefinition = {
  id: 'customer-personas',
  name: 'Customer Personas',
  description: 'Detailed user personas',
  category: 'market',

  systemPrompt: `You are a senior startup analyst. Generate detailed Customer Personas.

## Startup Idea
{idea}

## Target Customers
{targetCustomers}

## Output Format
### Customer Personas

#### Persona 1: [Name]
- **Role:** [Job title/role]
- **Age:** [Age range]
- **Location:** [Geographic location]
- **Bio:** [2-3 sentence background]
- **Goals:** [What they want to achieve]
- **Pain Points:** [Specific frustrations]
- **Tech Savviness:** [Low/Medium/High]
- **Willingness to Pay:** [Price sensitivity]
- **Quote:** "[Direct quote capturing their mindset]"

#### Persona 2: [Name]
[Same format as above]

#### Persona 3: [Name]
[Same format as above]

Create 2-3 distinct personas that represent different user types within your target market.`,

  dependencies: ['target-customers'],
  relevantFor: {},
  estimatedTokens: { input: 2000, output: 1000 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 45,
};
