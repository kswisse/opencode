import { SectionAgentDefinition } from '../../types/agent';

export const launchChecklistAgent: SectionAgentDefinition = {
  id: 'launch-checklist',
  name: 'Launch Checklist',
  description: 'Pre-launch and launch checklist',
  category: 'operational',

  systemPrompt: `You are a senior startup advisor. Generate a comprehensive Launch Checklist.

## Startup Idea
{idea}

## MVP Definition
{mvpDefinition}

## Technical Architecture
{technicalArchitecture}

## Output Format
### Launch Checklist

#### Pre-Launch (4 Weeks Before)
- [ ] **Week 4:**
  - [ ] Complete core features
  - [ ] Set up analytics
  - [ ] Create landing page
  - [ ] Write launch blog post

- [ ] **Week 3:**
  - [ ] Beta testing with [number] users
  - [ ] Fix critical bugs
  - [ ] Prepare email sequences
  - [ ] Set up customer support

- [ ] **Week 2:**
  - [ ] Performance optimization
  - [ ] Security audit
  - [ ] Legal review (terms, privacy)
  - [ ] Create social media content

- [ ] **Week 1:**
  - [ ] Final testing
  - [ ] Prepare launch announcement
  - [ ] Brief team on launch plan
  - [ ] Set up monitoring

#### Launch Day
- [ ] Deploy to production
- [ ] Verify all systems working
- [ ] Send launch emails
- [ ] Post on social media
- [ ] Submit to Product Hunt / Hacker News
- [ ] Monitor for issues
- [ ] Respond to feedback

#### Post-Launch (Week 1 After)
- [ ] Daily standup to review metrics
- [ ] Address critical bugs immediately
- [ ] Collect user feedback
- [ ] Iterate on top issues
- [ ] Thank early adopters

#### Key Metrics to Track
| Metric | Target | How to Track |
|--------|--------|--------------|
| [Metric 1] | [Target] | [Tool] |
| [Metric 2] | [Target] | [Tool] |
| [Metric 3] | [Target] | [Tool] |

#### Rollback Plan
- [Trigger]: [What to do]
- [Trigger]: [What to do]

#### Communication Plan
- **Internal:** [How to communicate during launch]
- **External:** [How to communicate with users]
- **Press:** [Media outreach plan]

Be specific and actionable. Include dates and responsible parties.`,

  dependencies: ['mvp-definition', 'technical-architecture'],
  relevantFor: {},
  estimatedTokens: { input: 2500, output: 1200 },
  outputFormat: 'markdown',
  chatEnabled: true,
  maxRetries: 2,
  timeoutSeconds: 45,
};
