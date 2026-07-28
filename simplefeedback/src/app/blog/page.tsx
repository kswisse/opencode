import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Blog - SimpleFeedback",
  description:
    "Product management insights, feedback best practices, and tips for building customer-centric products.",
};

const posts = [
  {
    slug: "how-to-collect-user-feedback-effectively",
    title: "How to Collect User Feedback Effectively",
    excerpt:
      "Learn the best practices for collecting actionable user feedback that drives product decisions.",
    date: "July 24, 2026",
    author: "Alex Mercer",
    authorRole: "Founder & CEO",
    readTime: "5 min read",
    tags: ["Best Practices", "User Research"],
  },
  {
    slug: "building-a-customer-centric-product-roadmap",
    title: "Building a Customer-Centric Product Roadmap",
    excerpt:
      "Discover how to build a product roadmap that balances business goals with customer needs.",
    date: "July 20, 2026",
    author: "Priya Sharma",
    authorRole: "Head of Product",
    readTime: "7 min read",
    tags: ["Product Management", "Roadmap"],
  },
  {
    slug: "why-ai-powered-feedback-analysis-changes-everything",
    title: "Why AI-Powered Feedback Analysis Changes Everything",
    excerpt:
      "How AI is transforming the way product teams process and act on user feedback at scale.",
    date: "July 15, 2026",
    author: "Jordan Lee",
    authorRole: "CTO",
    readTime: "6 min read",
    tags: ["AI", "Technology"],
  },
];

export default function BlogListing() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12">
      <h1 className="mb-2 text-4xl font-bold tracking-tight">Blog</h1>
      <p className="mb-12 text-lg text-neutral-600 dark:text-neutral-400">
        Product management insights, best practices, and tips from the SimpleFeedback team.
      </p>

      <div className="space-y-12">
        {posts.map((post) => (
          <article key={post.slug} className="group">
            <div className="flex items-center gap-3 text-sm text-neutral-500">
              <time>{post.date}</time>
              <span>&middot;</span>
              <span>{post.readTime}</span>
            </div>
            <Link href={`/blog/${post.slug}`}>
              <h2 className="mt-2 text-2xl font-bold group-hover:text-indigo-600 transition-colors">
                {post.title}
              </h2>
            </Link>
            <p className="mt-3 text-neutral-600 dark:text-neutral-400 leading-relaxed">
              {post.excerpt}
            </p>
            <div className="mt-4 flex items-center gap-3">
              <div className="flex items-center gap-2 text-sm text-neutral-500">
                <span className="font-medium">{post.author}</span>
                <span>&middot;</span>
                <span>{post.authorRole}</span>
              </div>
            </div>
            <div className="mt-3 flex gap-2">
              {post.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400"
                >
                  {tag}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
