import { SectionAgentDefinition } from '../../types/agent';

export const apiOverviewAgent: SectionAgentDefinition = {
  id: 'api-overview',
  name: 'API Overview',
  description: 'API design and endpoints',
  category: 'technical',

  systemPrompt: `You are a senior software architect. Generate a comprehensive API Overview.

## Startup Idea
{idea}

## Technical Architecture
{technicalArchitecture}

## Output Format
### API Overview

#### API Design Philosophy
[RESTful/GraphQL/gRPC — and why]

#### Authentication
[How API authentication works]

#### Core Endpoints
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/auth/register | Register new user | No |
| POST | /api/auth/login | Login user | No |
| GET | /api/users/me | Get current user | Yes |
| POST | /api/projects | Create project | Yes |
| GET | /api/projects/:id | Get project | Yes |
| POST | /api/projects/:id/generate | Start generation | Yes |
| POST | /api/projects/:id/sections/:sid/chat | Chat with section | Yes |

#### Data Models
- **CreateUserRequest:** email, password, name
- **Project:** id, idea, status, createdAt

#### Error Handling
| Status Code | Meaning | Action |
|-------------|---------|--------|
| 400 | Bad Request | Check request body |
| 401 | Unauthorized | Check auth token |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Retry or contact support |

#### Rate Limiting
- [Limit]: [Requests per window]

#### Versioning
[How API versions are managed]

Document the API contracts clearly for frontend integration.`,

  dependencies: ['technical-architecture'],
  relevantFor: {
    types: ['saas', 'platform', 'api', 'marketplace'],
  },
  estimatedTokens: { input: 3000, output: 1500 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 60,
};
