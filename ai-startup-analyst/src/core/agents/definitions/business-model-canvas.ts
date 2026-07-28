import { SectionAgentDefinition } from '../../types/agent';

export const businessModelCanvasAgent: SectionAgentDefinition = {
  id: 'business-model-canvas',
  name: 'Business Model Canvas',
  description: 'Business model overview',
  category: 'strategy',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Business Model Canvas.

## Startup Idea
{idea}

## Solution
{solution}

## Target Customers
{targetCustomers}

## Output Format
### Business Model Canvas

#### Key Partners
- [Partner 1]: [What they provide]
- [Partner 2]: [What they provide]
- [Partner 3]: [What they provide]

#### Key Activities
- [Activity 1]
- [Activity 2]
- [Activity 3]

#### Key Resources
- [Resource 1]: [Why it's critical]
- [Resource 2]: [Why it's critical]
- [Resource 3]: [Why it's critical]

#### Value Propositions
- [Value 1]: [How it solves customer pain]
- [Value 2]: [How it solves customer pain]
- [Value 3]: [How it solves customer pain]

#### Customer Relationships
- [Type]: [How you maintain relationships]

#### Channels
- [Channel 1]: [How you reach customers]
- [Channel 2]: [How you reach customers]

#### Customer Segments
- [Segment 1]: [Description]
- [Segment 2]: [Description]

#### Cost Structure
- Fixed costs: [List]
- Variable costs: [List]
- Key cost drivers: [List]

#### Revenue Streams
- [Stream 1]: [How it generates revenue]
- [Stream 2]: [How it generates revenue]

Fill out each section specifically for this startup.`,

  dependencies: ['solution', 'target-customers'],
  relevantFor: {},
  estimatedTokens: { input: 2500, output: 1500 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
