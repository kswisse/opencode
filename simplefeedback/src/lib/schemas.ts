import { z } from "zod";

// Feedback schemas
export const createFeedbackSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title must be 200 characters or less"),
  description: z.string().max(5000, "Description must be 5000 characters or less").optional().nullable(),
  projectId: z.string().min(1, "Project is required"),
});

export const updateFeedbackSchema = z.object({
  status: z.enum(["OPEN", "PLANNED", "IN_PROGRESS", "COMPLETED", "DECLINED"]).optional(),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]).optional(),
});

// Comment schemas
export const createCommentSchema = z.object({
  content: z.string().min(1, "Comment is required").max(5000, "Comment must be 5000 characters or less"),
});

// Project schemas
export const createProjectSchema = z.object({
  name: z.string().min(1, "Name is required").max(100, "Name must be 100 characters or less"),
  description: z.string().max(1000, "Description must be 1000 characters or less").optional().nullable(),
});

export const updateProjectSchema = z.object({
  name: z.string().min(1, "Name is required").max(100, "Name must be 100 characters or less").optional(),
  description: z.string().max(1000, "Description must be 1000 characters or less").optional().nullable(),
});

// Changelog schemas
export const createChangelogSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title must be 200 characters or less"),
  content: z.string().min(1, "Content is required").max(50000, "Content must be 50000 characters or less"),
  projectId: z.string().optional().nullable(),
  publish: z.boolean().optional(),
});

export const updateChangelogSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title must be 200 characters or less").optional(),
  content: z.string().min(1, "Content is required").max(50000, "Content must be 50000 characters or less").optional(),
  publish: z.boolean().optional(),
});

// Organization schemas
export const updateOrganizationSchema = z.object({
  orgName: z.string().min(1, "Organization name is required").max(100, "Organization name must be 100 characters or less").optional(),
  name: z.string().max(100, "Name must be 100 characters or less").optional(),
});

// Widget feedback schema
export const widgetFeedbackSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title must be 200 characters or less"),
  description: z.string().max(5000, "Description must be 5000 characters or less").optional().nullable(),
  email: z.string().email("Invalid email").optional().nullable(),
  name: z.string().max(100, "Name must be 100 characters or less").optional().nullable(),
  projectId: z.string().min(1, "Project is required"),
});

// Widget settings schema
export const widgetSettingsSchema = z.object({
  projectId: z.string().min(1, "Project is required"),
  buttonColor: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Invalid color hex").optional(),
  buttonText: z.string().max(50, "Button text must be 50 characters or less").optional(),
  position: z.enum(["left", "right"]).optional(),
  title: z.string().max(100, "Title must be 100 characters or less").optional(),
  subtitle: z.string().max(200, "Subtitle must be 200 characters or less").optional(),
});

// AI endpoint schemas
export const aiPrioritySchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title must be 200 characters or less"),
  description: z.string().max(5000).optional().nullable(),
  voteCount: z.number().int().min(0).max(1000000).optional().default(0),
});

export const aiDuplicatesSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title must be 200 characters or less"),
  description: z.string().max(5000).optional().nullable(),
});

// Organization update schema
export const updateOrganizationNameSchema = z.object({
  name: z.string().min(1, "Organization name is required").max(100, "Organization name must be 100 characters or less"),
});

// Setup organization schema
export const setupOrganizationSchema = z.object({
  userId: z.string().optional(),
  email: z.string().email("Invalid email"),
  name: z.string().max(100).optional().nullable(),
  orgName: z.string().min(1, "Organization name is required").max(100, "Organization name must be 100 characters or less"),
});
