import { SectionAgentDefinition } from '../../types/agent';

export const executiveSummaryAgent: SectionAgentDefinition = {
  id: 'executive-summary',
  name: 'Executive Summary',
  description: 'High-level overview of the startup opportunity',
  category: 'strategy',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Executive Summary.

## Startup Idea
{idea}

## Startup Characteristics
{characteristics}

## Output Format
### Executive Summary

#### Vision
[One sentence describing the vision]

#### Problem
[2-3 sentences about the problem being solved]

#### Solution
[2-3 sentences about the proposed solution]

#### Target Market
[2-3 sentences about the target market]

#### Key Differentiators
- [Differentiator 1]
- [Differentiator 2]
- [Differentiator 3]

#### Traction & Milestones
- [Key milestone 1]
- [Key milestone 2]

Be concise but comprehensive. Focus on what matters most to investors and stakeholders.`,

  dependencies: [],
  relevantFor: {},
  estimatedTokens: { input: 1500, output: 800 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 30,
};
