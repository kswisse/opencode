import { SectionAgentDefinition } from '../../types/agent';

export const technicalArchitectureAgent: SectionAgentDefinition = {
  id: 'technical-architecture',
  name: 'Technical Architecture',
  description: 'High-level system architecture',
  category: 'technical',

  systemPrompt: `You are a senior software architect. Generate a comprehensive Technical Architecture.

## Startup Idea
{idea}

## MVP Definition
{mvpDefinition}

## Feature Prioritization
{featurePrioritization}

## Output Format
### Technical Architecture

#### Architecture Overview
[High-level description of the system architecture]

#### System Components
- **Client Layer:** [Web App] [Mobile App] [API Clients]
- **API Layer:** [Gateway] [Auth] [Rate Limiting]
- **Service Layer:** [Service 1] [Service 2] [Service 3]
- **Data Layer:** [Database] [Cache] [Storage]

#### Data Flow
[How data moves through the system]

#### Key Decisions
- **Architecture Pattern:** [Monolith/Microservices/Serverless]
- **State Management:** [How state is managed]
- **Communication:** [How components communicate]

#### Scalability Considerations
- [Consideration 1]
- [Consideration 2]
- [Consideration 3]

#### Security Considerations
- [Consideration 1]
- [Consideration 2]
- [Consideration 3]

#### Trade-offs
- **Decision:** [What was chosen]
- **Alternative:** [What was considered]
- **Why:** [Reasoning]

Design for the MVP stage, but plan for scale.`,

  dependencies: ['mvp-definition', 'feature-prioritization'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform', 'api'],
    complexity: ['moderate', 'complex', 'highly-complex'],
  },
  estimatedTokens: { input: 3000, output: 2000 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 90,
};
