import { SectionAgentDefinition } from '../../types/agent';

export const databaseDesignAgent: SectionAgentDefinition = {
  id: 'database-design',
  name: 'Database Design',
  description: 'Conceptual data model',
  category: 'technical',

  systemPrompt: `You are a senior software architect. Generate a comprehensive Database Design.

## Startup Idea
{idea}

## Technical Architecture
{technicalArchitecture}

## Output Format
### Database Design

#### Entity Relationship Diagram
- **Users:** id (PK), email, name, createdAt, updatedAt
- **Projects:** id (PK), userId (FK), name, idea, status, createdAt, updatedAt

#### Key Entities
| Entity | Description | Key Fields |
|--------|-------------|------------|
| [Entity 1] | [What it represents] | [Important fields] |
| [Entity 2] | [What it represents] | [Important fields] |
| [Entity 3] | [What it represents] | [Important fields] |

#### Relationships
- [Entity 1] → [Entity 2]: [One-to-many/Many-to-many]
- [Entity 2] → [Entity 3]: [One-to-many/Many-to-many]

#### Indexes
- [Table]: [Index on column(s)] — [Why]

#### Data Types
- [Field]: [Type] — [Reasoning]

#### Scaling Considerations
- [Consideration 1]
- [Consideration 2]

Design for the MVP, but consider future scaling needs.`,

  dependencies: ['technical-architecture'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform', 'api'],
  },
  estimatedTokens: { input: 3000, output: 2000 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 90,
};
