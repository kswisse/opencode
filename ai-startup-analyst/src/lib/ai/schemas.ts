import { z } from 'zod';

export const generateParamsSchema = z.object({
  system: z.string().min(1),
  user: z.string().min(1),
  maxTokens: z.number().int().positive(),
  temperature: z.number().min(0).max(2).optional(),
  timeout: z.number().int().positive().optional(),
});

export const generateResultSchema = z.object({
  content: z.string(),
  usage: z.object({
    input: z.number().int(),
    output: z.number().int(),
  }),
  model: z.string(),
  finishReason: z.enum(['stop', 'length', 'timeout', 'error']),
});
