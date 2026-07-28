import { SectionAgentDefinition } from '../../types/agent';

export const mvpDefinitionAgent: SectionAgentDefinition = {
  id: 'mvp-definition',
  name: 'MVP Definition',
  description: 'Minimum viable product scope',
  category: 'operational',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive MVP Definition.

## Startup Idea
{idea}

## Solution
{solution}

## Feature Prioritization
{featurePrioritization}

## Output Format
### MVP Definition

#### MVP Vision
[One sentence describing what the MVP achieves]

#### Core Features (Must Have)
1. **[Feature 1]:** [Description and scope]
2. **[Feature 2]:** [Description and scope]
3. **[Feature 3]:** [Description and scope]

#### Nice to Have (V2)
- [Feature 1]
- [Feature 2]

#### Out of Scope (For Now)
- [Feature 1]: [Why it's excluded]
- [Feature 2]: [Why it's excluded]

#### User Stories
- As a [user type], I want to [action] so that [benefit]
- As a [user type], I want to [action] so that [benefit]
- As a [user type], I want to [action] so that [benefit]

#### Success Criteria
- [Metric 1]: [Target]
- [Metric 2]: [Target]
- [Metric 3]: [Target]

#### Technical Constraints
- [Constraint 1]
- [Constraint 2]
- [Constraint 3]

#### Timeline
- Week 1-2: [What gets built]
- Week 3-4: [What gets built]
- Week 5-6: [What gets built]

Define MVP as the smallest thing that validates the core hypothesis.`,

  dependencies: ['solution', 'feature-prioritization'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform'],
  },
  estimatedTokens: { input: 2000, output: 1000 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 45,
};
