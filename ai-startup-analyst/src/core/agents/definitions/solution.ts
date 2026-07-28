import { SectionAgentDefinition } from '../../types/agent';

export const solutionAgent: SectionAgentDefinition = {
  id: 'solution',
  name: 'Solution',
  description: 'How the startup solves the problem',
  category: 'strategy',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Solution section.

## Startup Idea
{idea}

## Startup Characteristics
{characteristics}

## Output Format
### Solution

#### Core Value Proposition
[One sentence: what you do and for whom]

#### How It Works
[Step-by-step explanation of the user journey]

#### Key Features
- [Feature 1]: [Brief description]
- [Feature 2]: [Brief description]
- [Feature 3]: [Brief description]

#### Technology Approach
[High-level technical approach]

#### Unique Advantages
[What makes this solution better than alternatives]

Be specific about the solution mechanics. Show understanding of the technical implementation.`,

  dependencies: [],
  relevantFor: {},
  estimatedTokens: { input: 1500, output: 800 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 30,
};
