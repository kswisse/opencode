import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

interface BlogPost {
  slug: string;
  title: string;
  content: string;
  date: string;
  author: string;
  authorRole: string;
  readTime: string;
  tags: string[];
  description: string;
}

const posts: BlogPost[] = [
  {
    slug: "how-to-collect-user-feedback-effectively",
    title: "How to Collect User Feedback Effectively",
    description:
      "Learn the best practices for collecting actionable user feedback that drives product decisions.",
    date: "July 24, 2026",
    author: "Alex Mercer",
    authorRole: "Founder & CEO",
    readTime: "5 min read",
    tags: ["Best Practices", "User Research"],
    content: `
## Why Feedback Matters

User feedback is the lifeblood of product development. Without it, you're building in the dark — guessing what users want, hoping you're right, and often discovering too late that you've invested time in the wrong features.

But collecting feedback effectively is harder than it sounds. Most companies make one of two mistakes: they either collect too little feedback to make informed decisions, or they collect so much that they can't process it all.

## Best Practices for Collecting Feedback

### 1. Make It Easy to Give Feedback

The harder it is for users to give feedback, the less feedback you'll receive. Reduce friction by:

- Embedding a feedback widget directly in your app (like SimpleFeedback's one-line JavaScript embed)
- Asking for feedback at the right moments (after completing a task, not in the middle of one)
- Keeping forms short — title and description are often enough

### 2. Provide Public Transparency

Users are more likely to give feedback when they can see it's being acted on. A public feedback board shows:

- What other users are requesting
- Which items are being planned or worked on
- That their feedback won't disappear into a black hole

### 3. Use AI to Manage Volume

If you have more than a handful of users, you'll get more feedback than your team can manually process. AI can help by:

- Automatically detecting duplicate submissions
- Scoring priority based on content and vote counts
- Clustering related feedback into themes
- Generating release notes from completed items

### 4. Close the Loop

Always follow up with users who submit feedback. Let them know:

- Their feedback was received
- What status it has (planned, in progress, completed)
- When they can expect to see changes

This simple practice turns a transactional feedback submission into a relationship-building moment.

## Common Mistakes to Avoid

- **Collecting feedback but never acting on it** — This erodes trust faster than not collecting feedback at all.
- **Only listening to loud voices** — A few vocal users don't represent your entire user base. Use voting and data to balance input.
- **Treating all feedback equally** — Not all feedback has the same business impact. Use prioritization frameworks to decide what to build.

## Measuring Success

Track these metrics to measure your feedback effectiveness:

- **Response rate** — What percentage of users submit feedback?
- **Time to acknowledge** — How quickly do you respond to submissions?
- **Time to action** — How long does it take from submission to completion?
- **User satisfaction** — Do users feel heard? Survey them periodically.

## Conclusion

Effective feedback collection isn't about having the most sophisticated system — it's about creating a continuous loop where users share input, teams act on it, and users see the results. SimpleFeedback is designed to make this loop as seamless as possible.

Ready to improve your feedback workflow? [Start your free trial](/signup) today.
    `.trim(),
  },
  {
    slug: "building-a-customer-centric-product-roadmap",
    title: "Building a Customer-Centric Product Roadmap",
    description:
      "Discover how to build a product roadmap that balances business goals with customer needs.",
    date: "July 20, 2026",
    author: "Priya Sharma",
    authorRole: "Head of Product",
    readTime: "7 min read",
    tags: ["Product Management", "Roadmap"],
    content: `
## What Makes a Roadmap Customer-Centric?

A customer-centric roadmap doesn't just list features — it tells a story about how those features will improve your users' lives. It balances what customers are asking for with your product vision and business goals.

## The Four Pillars of a Great Roadmap

### 1. Transparency

Your users shouldn't have to guess what you're building next. A public roadmap builds trust and reduces the "Is this product dead?" questions that plague less transparent companies.

Show:
- What you're working on now
- What's planned for the near future
- What's under consideration
- What you've decided not to pursue (and why)

### 2. Prioritization Framework

Use a consistent framework to decide what goes on the roadmap. We recommend a weighted model that considers:

- **User impact** — How many users will benefit? How much?
- **Business value** — Does this drive revenue, retention, or acquisition?
- **Effort** — How complex is this to build?
- **Strategic alignment** — Does this move us toward our product vision?

### 3. Feedback Integration

Your roadmap should be directly connected to your feedback system. Every item on your roadmap should trace back to user feedback — whether it's a direct request, a pattern you've observed, or a problem you've identified through user research.

### 4. Iteration and Flexibility

A roadmap is a living document. Set expectations that priorities can shift based on new information, market changes, or user needs.

## From Feedback to Roadmap

Here's how we recommend turning feedback into roadmap items:

1. **Collect** — Gather feedback from all channels (widget, email, support, etc.)
2. **Analyze** — Use AI to detect duplicates, cluster themes, and score priority
3. **Decide** — Review the highest-priority items in your weekly product review
4. **Schedule** — Add selected items to your roadmap with target timeframes
5. **Communicate** — Update the feedback submitter and your public board
6. **Ship and Celebrate** — When items are complete, publish changelogs

## Tools for the Job

A good roadmap tool should:

- Sync with your feedback system
- Support multiple views (public and internal)
- Allow voting to gauge interest
- Integrate with your development workflow

SimpleFeedback's roadmap does all of this — [try it for free](/signup).

## Conclusion

Building a customer-centric roadmap isn't about saying yes to every request. It's about making informed decisions and communicating them transparently. When your users understand how and why decisions are made, they trust you more — even when you say no.
    `.trim(),
  },
  {
    slug: "why-ai-powered-feedback-analysis-changes-everything",
    title: "Why AI-Powered Feedback Analysis Changes Everything",
    description:
      "How AI is transforming the way product teams process and act on user feedback at scale.",
    date: "July 15, 2026",
    author: "Jordan Lee",
    authorRole: "CTO",
    readTime: "6 min read",
    tags: ["AI", "Technology"],
    content: `
## The Feedback Problem

Here's a scenario every product manager knows well: your product has 10,000 active users, and 5% of them submit feedback each month. That's 500 pieces of feedback — titles, descriptions, feature requests, bug reports, and random thoughts.

Even reading through 500 submissions takes hours. Identifying duplicates? More hours. Clustering related requests? Even more. Prioritizing? That's a full-time job in itself.

This is where AI changes everything.

## How AI Transforms Feedback Processing

### 1. Automatic Duplicate Detection

Our AI analyzes each new feedback submission against existing items using semantic similarity. It doesn't just look for matching keywords — it understands meaning.

When a user submits "Would love dark mode support" and another user previously submitted "Please add a dark theme option," the AI recognizes these as duplicates and links them automatically.

### 2. Intelligent Priority Scoring

Not all feedback is equally important. Our AI scores each item from 0-100 based on:

- Language urgency ("critical", "blocking", "deal-breaker")
- User influence (voting patterns, submission history)
- Business impact (how many users are affected)
- Strategic alignment (matches your product goals)

This helps teams focus on what matters most, not what's loudest.

### 3. Smart Clustering

Related feedback naturally forms themes — performance improvements, UI enhancements, integration requests. Our AI automatically groups similar items into clusters, giving you a bird's-eye view of what your users want.

Instead of a firehose of individual requests, you see clear themes:
- "Performance & Speed" — 45 related items
- "Mobile Experience" — 38 related items
- "Integrations" — 27 related items

### 4. Automated Release Notes

When feedback items are completed, our AI generates release notes that are human-readable and organized by category. No more asking engineers to write release notes — they're generated automatically from completed items.

## The Results

Teams using AI-powered feedback analysis typically see:

- **80% reduction** in time spent processing feedback
- **60% improvement** in duplicate detection accuracy
- **3x faster** time from feedback to roadmap
- **90%+ user satisfaction** with the feedback process

## The Future

We're just scratching the surface of what AI can do for feedback management. Coming soon:

- Sentiment analysis to gauge user emotions
- Predictive modeling to forecast feature adoption
- Automated responses to acknowledge feedback
- Integration with LLMs for deeper analysis

## Get Started with AI-Powered Feedback

SimpleFeedback brings enterprise-grade AI analysis to teams of all sizes. Our Pro plan includes full AI features — duplicate detection, priority scoring, clustering, and automated release notes.

[Start your free trial](/signup) and see what AI can do for your feedback workflow.
    `.trim(),
  },
];

export async function generateStaticParams() {
  return posts.map((post) => ({
    slug: post.slug,
  }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = posts.find((p) => p.slug === slug);
  if (!post) return {};

  return {
    title: `${post.title} - SimpleFeedback Blog`,
    description: post.description,
    openGraph: {
      title: post.title,
      description: post.description,
      type: "article",
      publishedTime: post.date,
      authors: [post.author],
    },
  };
}

export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = posts.find((p) => p.slug === slug);

  if (!post) {
    notFound();
  }

  return (
    <article className="mx-auto max-w-3xl px-4 py-12">
      <Link
        href="/blog"
        className="mb-8 inline-flex items-center gap-1 text-sm text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-200"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Blog
      </Link>

      <header className="mb-8">
        <div className="flex items-center gap-3 text-sm text-neutral-500">
          <time>{post.date}</time>
          <span>&middot;</span>
          <span>{post.readTime}</span>
        </div>
        <h1 className="mt-3 text-4xl font-bold tracking-tight">{post.title}</h1>
        <div className="mt-4 flex items-center gap-2 text-sm text-neutral-500">
          <span className="font-medium">{post.author}</span>
          <span>&middot;</span>
          <span>{post.authorRole}</span>
        </div>
        <div className="mt-4 flex gap-2">
          {post.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400"
            >
              {tag}
            </span>
          ))}
        </div>
      </header>

      <div className="prose prose-sm max-w-none dark:prose-invert">
        {post.content.split("\n").map((line, i) => {
          if (line.startsWith("## ")) {
            return (
              <h2 key={i} className="mt-8 mb-4 text-xl font-bold">
                {line.replace("## ", "")}
              </h2>
            );
          }
          if (line.startsWith("### ")) {
            return (
              <h3 key={i} className="mt-6 mb-3 text-lg font-semibold">
                {line.replace("### ", "")}
              </h3>
            );
          }
          if (line.startsWith("- **")) {
            const match = line.match(/- \*\*(.+?)\*\*(.*)/);
            if (match) {
              return (
                <li key={i} className="ml-4 list-disc">
                  <strong>{match[1]}</strong>
                  {match[2]}
                </li>
              );
            }
          }
          if (line.startsWith("- ")) {
            return (
              <li key={i} className="ml-4 list-disc text-neutral-600 dark:text-neutral-400">
                {line.replace("- ", "")}
              </li>
            );
          }
          if (line.match(/^\d+\./)) {
            return (
              <li key={i} className="ml-4 list-decimal text-neutral-600 dark:text-neutral-400">
                {line.replace(/^\d+\.\s*/, "")}
              </li>
            );
          }
          if (line.startsWith("[")) {
            const linkMatch = line.match(/\[(.+?)\]\((.+?)\)/);
            if (linkMatch) {
              return (
                <p key={i} className="my-2">
                  <a href={linkMatch[2]} className="text-indigo-600 underline">
                    {linkMatch[1]}
                  </a>
                </p>
              );
            }
          }
          if (line.trim() === "") {
            return <div key={i} className="h-4" />;
          }
          // Check for inline links
          const processedLine = line.replace(
            /\[(.+?)\]\((.+?)\)/g,
            '<a href="$2" class="text-indigo-600 underline">$1</a>'
          );
          return (
            <p
              key={i}
              className="my-2 leading-relaxed text-neutral-600 dark:text-neutral-400"
              dangerouslySetInnerHTML={{ __html: processedLine }}
            />
          );
        })}
      </div>

      <div className="mt-12 rounded-2xl border border-neutral-200 bg-neutral-50 p-8 text-center dark:border-neutral-800 dark:bg-neutral-900">
        <h2 className="mb-2 text-xl font-bold">Try SimpleFeedback Free</h2>
        <p className="mb-4 text-neutral-600 dark:text-neutral-400">
          Start collecting, organizing, and acting on user feedback today.
        </p>
        <a
          href="/signup"
          className="inline-flex items-center justify-center rounded-md bg-neutral-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-neutral-700 dark:bg-neutral-50 dark:text-neutral-900 dark:hover:bg-neutral-200"
        >
          Start Free Trial
        </a>
      </div>
    </article>
  );
}
