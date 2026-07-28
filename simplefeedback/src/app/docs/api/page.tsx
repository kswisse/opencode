import type { Metadata } from "next";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export const metadata: Metadata = {
  title: "API Reference - SimpleFeedback Docs",
  description: "Complete API reference for the SimpleFeedback REST API.",
};

const content = `# API Reference

The SimpleFeedback API allows you to programmatically manage feedback, projects, and more.

## Authentication

All API requests require authentication using an API key. Include your API key in the \`Authorization\` header:

\`\`\`
Authorization: Bearer your-api-key
\`\`\`

You can generate API keys from your dashboard under **Settings > API Keys**.

## Endpoints

### List Feedback

\`\`\`
GET /api/v1/feedback
\`\`\`

Returns a paginated list of feedback items for your organization.

**Query Parameters:**
- \`project_id\` (optional) — Filter by project
- \`status\` (optional) — Filter by status (\`OPEN\`, \`PLANNED\`, \`IN_PROGRESS\`, \`COMPLETED\`, \`DECLINED\`)
- \`page\` (optional) — Page number (default: 1)
- \`limit\` (optional) — Items per page (default: 20, max: 100)

**Response:**
\`\`\`json
{
  "data": [
    {
      "id": "clx...",
      "title": "Dark mode support",
      "description": "Would love to see dark mode",
      "status": "PLANNED",
      "priority": "HIGH",
      "votes": 42,
      "created_at": "2026-07-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
\`\`\`

### Create Feedback

\`\`\`
POST /api/v1/feedback
\`\`\`

**Request Body:**
\`\`\`json
{
  "title": "Dark mode support",
  "description": "Would love to see dark mode",
  "project_id": "clx...",
  "labels": ["ui", "enhancement"]
}
\`\`\`

### Get Feedback

\`\`\`
GET /api/v1/feedback/:id
\`\`\`

### Update Feedback

\`\`\`
PATCH /api/v1/feedback/:id
\`\`\`

### Delete Feedback

\`\`\`
DELETE /api/v1/feedback/:id
\`\`\`

## Rate Limiting

API requests are limited to 100 requests per minute per API key. The response headers include rate limit information:

- \`X-RateLimit-Limit\`
- \`X-RateLimit-Remaining\`
- \`X-RateLimit-Reset\`

## Errors

The API uses conventional HTTP response codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Server Error |
`;

export default function ApiPage() {
  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
