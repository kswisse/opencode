import type { Metadata } from "next";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export const metadata: Metadata = {
  title: "Getting Started - SimpleFeedback Docs",
  description: "Learn how to get started with SimpleFeedback.",
};

const content = `# Getting Started with SimpleFeedback

Welcome to SimpleFeedback! This guide will walk you through setting up your first feedback board, configuring the widget, and inviting your team.

## Quick Start

### 1. Create Your Account

Sign up at [simplefeedback.com/signup](/signup). You'll be asked to create an organization and your first project.

### 2. Set Up Your Feedback Board

Once logged in, navigate to your project settings to customize your feedback board:

- Add your brand logo and colors
- Write a welcome message
- Configure which fields users need to fill in
- Set up moderation rules

### 3. Add the Widget to Your Site

Add the feedback widget to your website or app with a single line of JavaScript:

\`\`\`html
<script
  src="https://cdn.simplefeedback.com/widget.js"
  data-org="your-org-slug"
  data-project="your-project-id"
></script>
\`\`\`

### 4. Invite Your Team

Go to **Settings > Team** to invite team members. They'll receive an email invitation to join your organization.

## Core Concepts

### Organizations

An organization represents your company or team. All projects, feedback, and settings are scoped to an organization.

### Projects

Projects help you organize feedback by product, feature area, or team. Each project has its own feedback board and settings.

### Feedback Items

Users submit feedback items with a title, description, and optional labels. Items can be voted on and commented on by other users.

### Statuses

Feedback items go through a lifecycle:
- **Open** — New submissions awaiting review
- **Planned** — Accepted for future development
- **In Progress** — Currently being worked on
- **Completed** — Shipped to users
- **Declined** — Not planned for development

## Next Steps

- [Install the widget](/docs/installation)
- [Explore the API](/docs/api)
- [Set up integrations](/docs/integrations)
`;

export default function DocsPage() {
  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
