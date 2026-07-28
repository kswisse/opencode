import type { Metadata } from "next";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export const metadata: Metadata = {
  title: "Widget Installation - SimpleFeedback Docs",
  description: "Learn how to install the SimpleFeedback widget on your website or application.",
};

const content = `# Widget Installation

The SimpleFeedback widget lets you collect feedback directly from your website or application with minimal setup.

## Standard Installation

Add the following script tag to your HTML, just before the closing \`</body>\` tag:

\`\`\`html
<script
  src="https://cdn.simplefeedback.com/widget.js"
  data-org="your-org-slug"
  data-project="your-project-id"
></script>
\`\`\`

Replace \`your-org-slug\` and \`your-project-id\` with your organization slug and project ID from your dashboard settings.

## React / Next.js

For React-based applications, use the widget component:

\`\`\`jsx
import { useEffect } from "react";

export function FeedbackWidget({ orgSlug, projectId }) {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://cdn.simplefeedback.com/widget.js";
    script.setAttribute("data-org", orgSlug);
    script.setAttribute("data-project", projectId);
    script.async = true;
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [orgSlug, projectId]);

  return null;
}
\`\`\`

## Configuration Options

Customize the widget using \`data-\` attributes:

| Attribute | Description | Default |
|-----------|-------------|---------|
| \`data-position\` | Widget position (\`left\`, \`right\`) | \`right\` |
| \`data-button-color\` | Button background color | \`#6366f1\` |
| \`data-button-text\` | Button label text | \`Feedback\` |
| \`data-title\` | Modal title | \`Share Feedback\` |
| \`data-subtitle\` | Modal subtitle | \`Help us improve\` |

## Advanced: Programmatic Trigger

You can also trigger the widget programmatically:

\`\`\`javascript
// Open the widget
window.SimpleFeedback.open();

// Close the widget
window.SimpleFeedback.close();
\`\`\`

## Troubleshooting

**Widget not appearing?**
- Verify your organization slug and project ID are correct
- Check that your domain is whitelisted in widget settings
- Ensure no ad blockers are interfering
- Check the browser console for error messages
`;

export default function InstallationPage() {
  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
