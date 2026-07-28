import { SectionAgentDefinition } from '../../types/agent';

export const problemStatementAgent: SectionAgentDefinition = {
  id: 'problem-statement',
  name: 'Problem Statement',
  description: 'Clear articulation of the problem being solved',
  category: 'strategy',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Problem Statement.

## Startup Idea
{idea}

## Startup Characteristics
{characteristics}

## Output Format
### Problem Statement

#### The Problem
[Clear, concise statement of the problem]

#### Who Has This Problem
[Target users/customers affected]

#### Current Solutions
[How people solve this problem today]

#### Why Current Solutions Fall Short
[Pain points with existing solutions]

#### Impact of the Problem
[Quantify the impact if possible - time lost, money wasted, etc.]

#### Opportunity
[Why solving this problem creates value]

Be specific and empathetic. Show you understand the user's pain.`,

  dependencies: [],
  relevantFor: {},
  estimatedTokens: { input: 1200, output: 600 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 30,
};
