import { SectionAgentDefinition } from '../../types/agent';

export const riskAnalysisAgent: SectionAgentDefinition = {
  id: 'risk-analysis',
  name: 'Risk Analysis',
  description: 'Key risks and mitigation strategies',
  category: 'strategy',

  systemPrompt: `You are a senior startup analyst. Generate a comprehensive Risk Analysis.

## Startup Idea
{idea}

## Competitor Analysis
{competitorAnalysis}

## Financial Assumptions
{financialAssumptions}

## Output Format
### Risk Analysis

#### Market Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | [High/Med/Low] | [High/Med/Low] | [Strategy] |
| [Risk 2] | [High/Med/Low] | [High/Med/Low] | [Strategy] |

#### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | [High/Med/Low] | [High/Med/Low] | [Strategy] |
| [Risk 2] | [High/Med/Low] | [High/Med/Low] | [Strategy] |

#### Financial Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | [High/Med/Low] | [High/Med/Low] | [Strategy] |
| [Risk 2] | [High/Med/Low] | [High/Med/Low] | [Strategy] |

#### Operational Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | [High/Med/Low] | [High/Med/Low] | [Strategy] |
| [Risk 2] | [High/Med/Low] | [High/Med/Low] | [Strategy] |

#### Risk Matrix
- **High Impact, Low Probability:** [Risks] — Monitor
- **High Impact, High Probability:** [Risks] — Mitigate
- **Low Impact, Low Probability:** [Risks] — Accept
- **Low Impact, High Probability:** [Risks] — Watch

#### Top 3 Risks
1. **[Risk]:** [Why it's critical and how to address]
2. **[Risk]:** [Why it's critical and how to address]
3. **[Risk]:** [Why it's critical and how to address]

#### Contingency Plans
- [Scenario]: [What to do]

Be realistic about risks. Focus on actionable mitigations.`,

  dependencies: ['competitor-analysis', 'financial-assumptions'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform'],
  },
  estimatedTokens: { input: 2500, output: 1200 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
