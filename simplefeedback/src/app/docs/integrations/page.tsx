import type { Metadata } from "next";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export const metadata: Metadata = {
  title: "Integrations - SimpleFeedback Docs",
  description: "Learn how to integrate SimpleFeedback with GitHub, Slack, and other tools.",
};

const content = `# Integrations

Connect SimpleFeedback with the tools you already use to streamline your workflow.

## GitHub Integration

Automatically create GitHub issues from high-priority feedback items.

### Setup

1. Go to **Settings > Integrations > GitHub**
2. Click "Connect GitHub Account"
3. Select the repositories you want to integrate
4. Set the priority threshold for automatic issue creation
5. Configure labels to apply to created issues

### How It Works

When a feedback item reaches your configured priority threshold, SimpleFeedback automatically:

1. Creates a GitHub issue with the feedback title and description
2. Applies configured labels (e.g., \`feedback\`, \`priority\`)
3. Links the GitHub issue back to the feedback item
4. Updates the feedback status when the issue is closed

## Slack Integration

Receive notifications about new feedback and status changes in Slack.

### Setup

1. Go to **Settings > Integrations > Slack**
2. Click "Add to Slack"
3. Select the channel for notifications
4. Configure which events trigger notifications

### Available Events

- New feedback submitted
- Feedback status changed
- High-priority feedback detected
- Weekly digest summary

## Webhooks

Build custom integrations with webhooks. Receive HTTP POST requests when events occur in your organization.

### Setup

1. Go to **Settings > Integrations > Webhooks**
2. Click "Add Webhook"
3. Enter your endpoint URL
4. Select the events to subscribe to
5. Copy the signing secret

### Payload Format

\`\`\`json
{
  "event": "feedback.created",
  "organization_id": "org_...",
  "data": {
    "id": "clx...",
    "title": "Dark mode support",
    "status": "OPEN"
  },
  "timestamp": "2026-07-26T12:00:00Z"
}
\`\`\`

## API Access

Business plan customers get full API access. See the [API Reference](/docs/api) for documentation.

## Coming Soon

- Zapier integration
- Jira integration
- Linear integration
- Discord integration
`;

export default function IntegrationsPage() {
  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
