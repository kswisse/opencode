import { SectionAgentDefinition } from '../../types/agent';

export const suggestedTechStackAgent: SectionAgentDefinition = {
  id: 'suggested-tech-stack',
  name: 'Suggested Tech Stack',
  description: 'Recommended technologies',
  category: 'technical',

  systemPrompt: `You are a senior software architect. Generate a comprehensive Suggested Tech Stack.

## Startup Idea
{idea}

## Technical Architecture
{technicalArchitecture}

## Output Format
### Suggested Tech Stack

#### Frontend
| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | [Technology] | [Reason] |
| UI Library | [Technology] | [Reason] |
| State | [Technology] | [Reason] |
| Styling | [Technology] | [Reason] |

#### Backend
| Layer | Technology | Why |
|-------|-----------|-----|
| Runtime | [Technology] | [Reason] |
| Framework | [Technology] | [Reason] |
| ORM | [Technology] | [Reason] |
| Auth | [Technology] | [Reason] |

#### Database
| Type | Technology | Why |
|------|-----------|-----|
| Primary DB | [Technology] | [Reason] |
| Cache | [Technology] | [Reason] |
| Search | [Technology] | [Reason] |

#### Infrastructure
| Service | Technology | Why |
|---------|-----------|-----|
| Hosting | [Technology] | [Reason] |
| CI/CD | [Technology] | [Reason] |
| Monitoring | [Technology] | [Reason] |
| Storage | [Technology] | [Reason] |

#### AI/ML (if applicable)
| Service | Technology | Why |
|---------|-----------|-----|
| LLM Provider | [Technology] | [Reason] |
| Vector DB | [Technology] | [Reason] |

#### Cost Estimate
- **Free Tier:** [What's available]
- **Estimated Monthly:** $[Amount] at [scale]

#### Why This Stack
[Overall reasoning for the tech choices]

Choose technologies that balance developer experience, scalability, and cost.`,

  dependencies: ['technical-architecture'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform', 'api'],
  },
  estimatedTokens: { input: 2500, output: 1500 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
