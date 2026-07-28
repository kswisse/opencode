import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../src/generated/prisma/client";

const connectionString = process.env.DATABASE_URL!;
const adapter = new PrismaPg({ connectionString });
const prisma = new PrismaClient({ adapter });

async function main() {
  console.log("Seeding database...");

  const org = await prisma.organization.upsert({
    where: { slug: "demo-company" },
    update: {},
    create: {
      name: "Demo Company",
      slug: "demo-company",
      subscription: {
        create: {
          plan: "PRO",
        },
      },
      users: {
        create: {
          email: "admin@demo.com",
          name: "Demo Admin",
          role: "ADMIN",
        },
      },
    },
  });

  console.log(`Created organization: ${org.name}`);

  const project = await prisma.project.upsert({
    where: { slug_organizationId: { slug: "general", organizationId: org.id } },
    update: {},
    create: {
      name: "General",
      description: "General feedback and feature requests",
      slug: "general",
      organizationId: org.id,
    },
  });

  console.log(`Created project: ${project.name}`);

  const user = await prisma.user.findFirst({
    where: { organizationId: org.id },
  });

  if (!user) throw new Error("No user found");

  const feedbackData = [
    { title: "Dark mode support", description: "Would love to see a dark mode option for the dashboard. It would make it much easier to use at night.", status: "PLANNED" as const, priority: "HIGH" as const },
    { title: "API integration with Slack", description: "It would be great to get feedback notifications directly in Slack so our team can respond faster.", status: "PLANNED" as const, priority: "HIGH" as const },
    { title: "Export to CSV", description: "Need the ability to export all feedback data to CSV for reporting to stakeholders each month.", status: "IN_PROGRESS" as const, priority: "MEDIUM" as const },
    { title: "Mobile app", description: "A mobile app would be awesome for checking feedback and responding on the go.", status: "OPEN" as const, priority: "MEDIUM" as const },
    { title: "Custom branding on public board", description: "Allow custom logo, colors, and fonts on the public feedback board to match our brand guidelines.", status: "OPEN" as const, priority: "HIGH" as const },
    { title: "Multiple voting per user", description: "Users should be able to vote multiple times on the same feature request to show strong interest. This would help us gauge true demand.", status: "DECLINED" as const, priority: "LOW" as const },
    { title: "Add search to feedback board", description: "The public feedback board needs a search bar so users can find existing requests before submitting duplicates.", status: "COMPLETED" as const, priority: "MEDIUM" as const },
    { title: "Email notifications for status changes", description: "Users should receive an email when the status of their feedback changes to keep them in the loop.", status: "COMPLETED" as const, priority: "HIGH" as const },
    { title: "SSO/SAML support", description: "Enterprise customers need SSO/SAML authentication to comply with their security policies.", status: "PLANNED" as const, priority: "HIGH" as const },
    { title: "Webhook integration", description: "Send webhook events when feedback is created or updated so we can integrate with our internal tools.", status: "OPEN" as const, priority: "MEDIUM" as const },
    { title: "Bulk import feedback", description: "Ability to import feedback in bulk from CSV or JSON for migrating from other tools.", status: "OPEN" as const, priority: "LOW" as const },
    { title: "Kanban board view", description: "A kanban-style view for managing feedback status would make it easier to visualize our workflow.", status: "OPEN" as const, priority: "MEDIUM" as const },
    { title: "User profile pages", description: "Public user profiles showing all feedback submitted and their voting history.", status: "DECLINED" as const, priority: "LOW" as const },
    { title: "API access for custom integrations", description: "REST API access for building custom integrations with our internal tools and workflows.", status: "IN_PROGRESS" as const, priority: "HIGH" as const },
    { title: "Automatic changelog publishing", description: "Auto-publish changelogs when feedback moves to completed status, with customizable templates.", status: "COMPLETED" as const, priority: "MEDIUM" as const },
  ];

  for (const fb of feedbackData) {
    const feedback = await prisma.feedback.create({
      data: {
        title: fb.title,
        description: fb.description,
        status: fb.status,
        priority: fb.priority,
        projectId: project.id,
        organizationId: org.id,
        authorId: user.id,
        aiPriorityScore: Math.random() * 100,
      },
    });

    const voteCount = Math.floor(Math.random() * 15) + 1;
    for (let i = 0; i < voteCount; i++) {
      await prisma.feedbackVote.create({
        data: {
          feedbackId: feedback.id,
          userId: user.id,
        },
      }).catch(() => {});
    }

    const commentCount = Math.floor(Math.random() * 3);
    for (let i = 0; i < commentCount; i++) {
      await prisma.feedbackComment.create({
        data: {
          content: ["Great idea!", "This would be very useful.", "I've been wanting this too!", "When will this be available?", "Thanks for considering this!"][i],
          feedbackId: feedback.id,
          userId: user.id,
        },
      });
    }
  }

  console.log(`Created ${feedbackData.length} feedback items`);

  await prisma.changelog.create({
    data: {
      title: "Initial Release v1.0",
      content: "## What's New\n\nWe're excited to announce the launch of SimpleFeedback!\n\n### Features\n\n- **Public Feedback Board** - Collect feedback from your users\n- **Roadmap** - Show your users what's planned and in progress\n- **Changelogs** - Keep users informed with release notes\n- **AI Priority Scoring** - Let AI help you prioritize feedback\n- **Embeddable Widget** - Add feedback collection to your app\n\n### Improvements\n\n- Fast and responsive UI\n- Real-time updates\n- Email notifications\n\n### Bug Fixes\n\n- Initial release",
      organizationId: org.id,
      projectId: project.id,
      publishedAt: new Date(),
    },
  });

  await prisma.feedbackEmbed.create({
    data: {
      organizationId: org.id,
      projectId: project.id,
      buttonColor: "#6366f1",
      buttonText: "Feedback",
      position: "right",
      title: "Share Feedback",
      subtitle: "Help us improve Demo Company",
    },
  });

  console.log("Seed completed successfully!");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
