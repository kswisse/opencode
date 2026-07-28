import { SectionAgentDefinition } from '../../types/agent';

export const swotAnalysisAgent: SectionAgentDefinition = {
  id: 'swot-analysis',
  name: 'SWOT Analysis',
  description: 'Strengths, Weaknesses, Opportunities, Threats',
  category: 'strategy',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive SWOT Analysis.

## Startup Idea
{idea}

## Problem Statement
{problemStatement}

## Solution
{solution}

## Output Format
### SWOT Analysis

#### Strengths (Internal, Positive)
1. [Strength 1]
2. [Strength 2]
3. [Strength 3]
4. [Strength 4]

#### Weaknesses (Internal, Negative)
1. [Weakness 1]
2. [Weakness 2]
3. [Weakness 3]
4. [Weakness 4]

#### Opportunities (External, Positive)
1. [Opportunity 1]
2. [Opportunity 2]
3. [Opportunity 3]
4. [Opportunity 4]

#### Threats (External, Negative)
1. [Threat 1]
2. [Threat 2]
3. [Threat 3]
4. [Threat 4]

#### Strategic Implications
- **Leverage Strengths:** [How to use strengths to capture opportunities]
- **Address Weaknesses:** [How to mitigate weaknesses]
- **Capitalize on Opportunities:** [Specific actions]
- **Mitigate Threats:** [Defensive strategies]

Be specific and realistic. Focus on factors unique to this startup.`,

  dependencies: ['problem-statement', 'solution'],
  relevantFor: {},
  estimatedTokens: { input: 2000, output: 1000 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 45,
};
