import { SectionAgentDefinition } from '../../types/agent';

export const goToMarketStrategyAgent: SectionAgentDefinition = {
  id: 'go-to-market-strategy',
  name: 'Go-to-Market Strategy',
  description: 'How to launch and acquire customers',
  category: 'operational',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Go-to-Market Strategy.

## Startup Idea
{idea}

## Target Customers
{targetCustomers}

## Competitor Analysis
{competitorAnalysis}

## Revenue Model
{revenueModel}

## Output Format
### Go-to-Market Strategy

#### Launch Phases
1. **Pre-Launch (Month -3 to 0)**
   - [Action 1]
   - [Action 2]
   - [Action 3]

2. **Launch (Month 0 to 1)**
   - [Action 1]
   - [Action 2]
   - [Action 3]

3. **Post-Launch (Month 1 to 3)**
   - [Action 1]
   - [Action 2]
   - [Action 3]

#### Channel Strategy
| Channel | Purpose | Budget | Expected CAC |
|---------|---------|--------|--------------|
| [Channel 1] | [Purpose] | $[Budget] | $[CAC] |
| [Channel 2] | [Purpose] | $[Budget] | $[CAC] |

#### Growth Hacks
- [Hack 1]: [Description]
- [Hack 2]: [Description]
- [Hack 3]: [Description]

#### Content Strategy
- **Blog:** [Topics and frequency]
- **Social:** [Platforms and approach]
- **Email:** [Sequence and goals]
- **Community:** [Building and nurturing]

#### Partnerships
- [Partner type 1]: [How they help]
- [Partner type 2]: [How they help]

#### Success Metrics
- Month 1: [Target]
- Month 3: [Target]
- Month 6: [Target]

Be specific and actionable. Include timelines and metrics.`,

  dependencies: ['target-customers', 'competitor-analysis', 'revenue-model'],
  relevantFor: {},
  estimatedTokens: { input: 2500, output: 1500 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
