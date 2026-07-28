import { SectionAgentDefinition } from '../../types/agent';

export const targetCustomersAgent: SectionAgentDefinition = {
  id: 'target-customers',
  name: 'Target Customers',
  description: 'Who the startup serves',
  category: 'market',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Target Customers section.

## Startup Idea
{idea}

## Startup Characteristics
{characteristics}

## Output Format
### Target Customers

#### Primary Target
[Main customer segment with description]

#### Secondary Target
[Additional customer segment]

#### Customer Profile
- Demographics: [Age, location, income, etc.]
- Psychographics: [Values, interests, behaviors]
- Pain Points: [Specific problems they face]
- Goals: [What they want to achieve]

#### Customer Segments
| Segment | Size | Priority | Why |
|---------|------|----------|-----|
| [Segment 1] | [Size] | [High/Med/Low] | [Reason] |
| [Segment 2] | [Size] | [High/Med/Low] | [Reason] |

#### Where to Find Them
[Channels, communities, platforms where target customers congregate]

Be specific about who these customers are and why they matter.`,

  dependencies: [],
  relevantFor: {},
  estimatedTokens: { input: 1200, output: 600 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 30,
};
