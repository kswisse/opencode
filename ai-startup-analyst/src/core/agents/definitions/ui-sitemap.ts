import { SectionAgentDefinition } from '../../types/agent';

export const uiSitemapAgent: SectionAgentDefinition = {
  id: 'ui-sitemap',
  name: 'UI Sitemap',
  description: 'Site structure and navigation',
  category: 'technical',

  systemPrompt: `You are a senior UX architect. Generate a comprehensive UI Sitemap.

## Startup Idea
{idea}

## MVP Definition
{mvpDefinition}

## Output Format
### UI Sitemap

#### Site Architecture
- **Home**
  - Landing Page: Hero Section, Features, Pricing, CTA
  - Auth: Login, Register, Forgot Password
  - Dashboard: Projects List, Project Detail, Workspace, Sections, Section Detail + Chat, Settings, Profile
  - Settings: Account, Billing, API Keys
  - Help: Documentation, Support

#### Key Pages
| Page | Purpose | Key Elements |
|------|---------|--------------|
| [Page 1] | [Purpose] | [Elements] |
| [Page 2] | [Purpose] | [Elements] |

#### Navigation Flow
[How users move between pages]

#### Mobile Considerations
[How the navigation works on mobile]

#### Accessibility
[Key accessibility considerations]

Design for clarity and ease of use.`,

  dependencies: ['mvp-definition'],
  relevantFor: {
    types: ['marketplace', 'saas', 'e-commerce', 'fintech', 'healthtech', 'edtech', 'social', 'platform'],
  },
  estimatedTokens: { input: 2000, output: 1000 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 45,
};
