# ResearchOS — Backend Architecture Specification

> **For agentic workers:** This is the architectural blueprint for ResearchOS. Implementation should follow this spec task-by-task using TDD.

**Goal:** Design a production-grade Research Operating System that orchestrates multiple AI agents to execute long-running scientific research projects with persistent state, human approval gates, and crash recovery.

**Architecture:** Local-first modular monolith using SQLite for persistence, file-system artifacts in Markdown, Git for version control, and a plugin-based agent orchestration layer. Phase-based execution with checkpoints enables resume-after-interruption. All state survives process crashes.

**Tech Stack:** TypeScript, Drizzle ORM, SQLite (via `better-sqlite3`), Markdown (via `unified`/`remark`), Git (via `simple-git`), Zod for validation, Pino for logging, Node.js worker threads for agent execution.

---

## Table of Contents

1. [Complete Folder Structure](#1-complete-folder-structure)
2. [Data Models — TypeScript Types](#2-data-models--typescript-types)
3. [Database Schema — Drizzle ORM](#3-database-schema--drizzle-orm)
4. [Storage Architecture](#4-storage-architecture)
5. [API Design — Internal Module APIs](#5-api-design--internal-module-apis)
6. [CLI Interface](#6-cli-interface)
7. [Configuration System](#7-configuration-system)
8. [Module Responsibilities](#8-module-responsibilities)
9. [Module Dependency Graph](#9-module-dependency-graph)
10. [Error Handling Strategy](#10-error-handling-strategy)
11. [Observability](#11-observability)
12. [Security Boundaries](#12-security-boundaries)
13. [Key Architectural Decisions](#13-key-architectural-decisions)

---

## 1. Complete Folder Structure

```
researchos/
├── .gitignore
├── .env.example
├── package.json
├── tsconfig.json
├── drizzle.config.ts
├── README.md
│
├── src/
│   ├── index.ts                          # Entry point — bootstraps all modules
│   ├── cli.ts                            # CLI entry point (commander-based)
│   ├── http.ts                           # Optional HTTP API server (express/hono)
│   │
│   ├── core/                             # Core domain types and utilities
│   │   ├── types.ts                      # All shared TypeScript types/interfaces
│   │   ├── errors.ts                     # Custom error classes
│   │   ├── result.ts                     # Result<T, E> monad for error handling
│   │   ├── events.ts                     # Internal event bus types
│   │   ├── clock.ts                      # Abstract clock for testability
│   │   ├── id.ts                         # UUID generation utilities
│   │   └── logger.ts                     # Pino logger factory
│   │
│   ├── db/                               # Database layer
│   │   ├── index.ts                      # Database connection singleton
│   │   ├── schema/                       # Drizzle schema definitions
│   │   │   ├── projects.ts
│   │   │   ├── phases.ts
│   │   │   ├── evidence.ts
│   │   │   ├── memory.ts
│   │   │   ├── sessions.ts
│   │   │   ├── workflows.ts
│   │   │   ├── audit.ts
│   │   │   └── index.ts                  # Re-exports all schemas
│   │   ├── migrations/                   # Drizzle migration files
│   │   │   └── 0000_initial.sql
│   │   ├── seed.ts                       # Database seeding for dev
│   │   └── connection.ts                 # SQLite connection with WAL mode
│   │
│   ├── storage/                          # File-system storage layer
│   │   ├── index.ts                      # Storage service interface
│   │   ├── artifact-store.ts             # Markdown artifact read/write
│   │   ├── git-store.ts                  # Git integration for versioning
│   │   ├── path-builder.ts              # Deterministic path resolution
│   │   └── paths.ts                      # Path constants and helpers
│   │
│   ├── memory/                           # Memory subsystem
│   │   ├── index.ts                      # Memory manager interface
│   │   ├── short-term.ts                 # Working memory (current phase context)
│   │   ├── long-term.ts                  # Persistent knowledge store
│   │   ├── episodic.ts                   # Research event history
│   │   ├── retrieval.ts                  # Memory search and retrieval
│   │   └── summarizer.ts                 # Memory compression/summarization
│   │
│   ├── agents/                           # Agent orchestration
│   │   ├── index.ts                      # Agent orchestrator interface
│   │   ├── orchestrator.ts               # Phase execution coordinator
│   │   ├── executor.ts                   # Single agent task executor
│   │   ├── pool.ts                       # Agent process/thread pool
│   │   ├── registry.ts                   # Agent type registry
│   │   ├── models/                       # Model provider integrations
│   │   │   ├── types.ts                  # Unified model interface
│   │   │   ├── openai.ts                 # OpenAI/compatible providers
│   │   │   ├── anthropic.ts              # Anthropic Claude
│   │   │   ├── ollama.ts                 # Local Ollama
│   │   │   ├── fallback.ts               # Fallback/circuit breaker wrapper
│   │   │   └── index.ts                  # Provider factory
│   │   └── prompts/                      # Prompt templates
│   │       ├── planner.md
│   │       ├── researcher.md
│   │       ├── analyst.md
│   │       └── reviewer.md
│   │
│   ├── workflow/                          # Workflow engine
│   │   ├── index.ts                      # Workflow engine interface
│   │   ├── dag.ts                        # DAG validation and execution
│   │   ├── scheduler.ts                  # Task scheduling with dependencies
│   │   ├── checkpoint.ts                # Checkpoint/resume logic
│   │   └── templates/                    # Built-in workflow templates
│   │       ├── literature-review.ts
│   │       ├── experiment.ts
│   │       └── meta-analysis.ts
│   │
│   ├── approval/                          # Human-in-the-loop
│   │   ├── index.ts                      # Approval gate interface
│   │   ├── gate.ts                       # Phase transition approval logic
│   │   ├── review-ui.ts                  # Review artifact generation
│   │   └── history.ts                    # Approval decision audit
│   │
│   ├── evidence/                          # Evidence management
│   │   ├── index.ts                      # Evidence service interface
│   │   ├── collector.ts                  # Evidence collection from agents
│   │   ├── citation.ts                   # Citation formatting (APA, MLA, etc.)
│   │   ├── confidence.ts                 # Confidence scoring
│   │   └── validator.ts                  # Evidence quality checks
│   │
│   ├── plugins/                           # Plugin system
│   │   ├── index.ts                      # Plugin manager interface
│   │   ├── loader.ts                     # Dynamic plugin loading
│   │   ├── sandbox.ts                    # Plugin isolation
│   │   └── types.ts                      # Plugin API contract
│   │
│   ├── config/                            # Configuration management
│   │   ├── index.ts                      # Config loader interface
│   │   ├── schema.ts                     # Zod schemas for all config
│   │   ├── loader.ts                     # File + env + CLI config merging
│   │   ├── defaults.ts                   # Default configuration values
│   │   └── validator.ts                  # Config validation
│   │
│   └── http/                              # HTTP API layer (optional)
│       ├── index.ts                      # Server setup
│       ├── routes/                       # Route handlers
│       │   ├── projects.ts
│       │   ├── phases.ts
│       │   ├── evidence.ts
│       │   ├── memory.ts
│       │   ├── sessions.ts
│       │   ├── health.ts
│       │   └── ws.ts                     # WebSocket for real-time updates
│       ├── middleware/                    # HTTP middleware
│       │   ├── auth.ts
│       │   ├── rate-limit.ts
│       │   ├── error-handler.ts
│       │   └── request-id.ts
│       └── openapi.ts                    # OpenAPI spec generation
│
├── data/                                 # Runtime data directory (gitignored)
│   ├── researchos.db                    # SQLite database
│   ├── researchos.db-wal                # WAL journal
│   ├── researchos.db-shm                # Shared memory file
│   └── logs/                             # Log files
│       └── researchos.log
│
├── projects/                             # Research project workspaces
│   └── {project-id}/                     # One directory per project
│       ├── .git/                         # Per-project git repo (or use main repo)
│       ├── project.md                    # Project metadata (markdown)
│       ├── phases/
│       │   └── {phase-id}/
│       │       ├── phase.md              # Phase definition
│       │       ├── status.md             # Current status
│       │       ├── artifacts/            # Phase outputs
│       │       │   ├── report.md
│       │       │   └── data.json
│       │       └── evidence/             # Collected evidence
│       │           ├── source-001.md
│       │           └── source-002.md
│       ├── memory/
│       │   ├── short-term.md             # Current working context
│       │   ├── long-term/
│       │   │   ├── findings.md
│       │   │   └── methods.md
│       │   └── episodic/
│       │       └── log.md                # Chronological event log
│       └── checkpoints/
│           ├── checkpoint-001.json
│           └── checkpoint-002.json
│
├── plugins/                              # User-installed plugins
│   └── .gitkeep
│
├── templates/                            # Built-in workflow templates
│   ├── literature-review.yaml
│   ├── experiment-design.yaml
│   └── meta-analysis.yaml
│
└── tests/                                # Test suite
    ├── unit/
    │   ├── db/
    │   ├── memory/
    │   ├── agents/
    │   ├── workflow/
    │   ├── evidence/
    │   └── config/
    ├── integration/
    │   ├── project-lifecycle.test.ts
    │   ├── phase-execution.test.ts
    │   └── crash-recovery.test.ts
    ├── fixtures/
    │   ├── projects/
    │   └── configs/
    └── helpers/
        └── test-db.ts
```

---

## 2. Data Models — TypeScript Types

```typescript
// src/core/types.ts

import { z } from "zod";

// ─── Branded Types ────────────────────────────────────────────────────────────

export type ProjectId = string & { readonly __brand: "ProjectId" };
export type PhaseId = string & { readonly __brand: "PhaseId" };
export type EvidenceId = string & { readonly __brand: "EvidenceId" };
export type MemoryId = string & { readonly __brand: "MemoryId" };
export type SessionId = string & { readonly __brand: "SessionId" };
export type WorkflowId = string & { readonly __brand: "WorkflowId" };
export type AuditId = string & { readonly __brand: "AuditId" };
export type CheckpointId = string & { readonly __brand: "CheckpointId" };

export function projectId(raw: string): ProjectId {
  return raw as ProjectId;
}
export function phaseId(raw: string): PhaseId {
  return raw as PhaseId;
}
export function evidenceId(raw: string): EvidenceId {
  return raw as EvidenceId;
}
export function memoryId(raw: string): MemoryId {
  return raw as MemoryId;
}
export function sessionId(raw: string): SessionId {
  return raw as SessionId;
}
export function workflowId(raw: string): WorkflowId {
  return raw as WorkflowId;
}
export function auditId(raw: string): AuditId {
  return raw as AuditId;
}
export function checkpointId(raw: string): CheckpointId {
  return raw as CheckpointId;
}

// ─── Enums ────────────────────────────────────────────────────────────────────

export const ProjectStatus = {
  DRAFT: "draft",
  ACTIVE: "active",
  PAUSED: "paused",
  COMPLETED: "completed",
  FAILED: "failed",
  ARCHIVED: "archived",
} as const;
export type ProjectStatus = (typeof ProjectStatus)[keyof typeof ProjectStatus];

export const PhaseStatus = {
  PENDING: "pending",
  RUNNING: "running",
  AWAITING_APPROVAL: "awaiting_approval",
  APPROVED: "approved",
  REJECTED: "rejected",
  COMPLETED: "completed",
  FAILED: "failed",
  SKIPPED: "skipped",
} as const;
export type PhaseStatus = (typeof PhaseStatus)[keyof typeof PhaseStatus];

export const MemoryType = {
  SHORT_TERM: "short_term",
  LONG_TERM: "long_term",
  EPISODIC: "episodic",
} as const;
export type MemoryType = (typeof MemoryType)[keyof typeof MemoryType];

export const EvidenceConfidence = {
  HIGH: "high",
  MEDIUM: "medium",
  LOW: "low",
  SPECULATIVE: "speculative",
} as const;
export type EvidenceConfidence =
  (typeof EvidenceConfidence)[keyof typeof EvidenceConfidence];

export const AgentRole = {
  PLANNER: "planner",
  RESEARCHER: "researcher",
  ANALYST: "analyst",
  REVIEWER: "reviewer",
  CUSTOM: "custom",
} as const;
export type AgentRole = (typeof AgentRole)[keyof typeof AgentRole];

export const AuditAction = {
  PROJECT_CREATED: "project_created",
  PROJECT_UPDATED: "project_updated",
  PHASE_STARTED: "phase_started",
  PHASE_COMPLETED: "phase_completed",
  PHASE_APPROVED: "phase_approved",
  PHASE_REJECTED: "phase_rejected",
  EVIDENCE_COLLECTED: "evidence_collected",
  MEMORY_WRITTEN: "memory_written",
  AGENT_INVOKED: "agent_invoked",
  AGENT_COMPLETED: "agent_completed",
  AGENT_FAILED: "agent_failed",
  CHECKPOINT_SAVED: "checkpoint_saved",
  CHECKPOINT_RESTORED: "checkpoint_restored",
  CONFIG_CHANGED: "config_changed",
  PLUGIN_LOADED: "plugin_loaded",
} as const;
export type AuditAction = (typeof AuditAction)[keyof typeof AuditAction];

// ─── Domain Models ────────────────────────────────────────────────────────────

/** Research project — top-level entity */
export interface ResearchProject {
  id: ProjectId;
  name: string;
  description: string;
  status: ProjectStatus;
  goal: string; // Research question or objective
  hypothesis: string | null;
  methodology: string | null;
  tags: string[]; // JSON-serialized in DB
  config: ProjectConfig; // JSON-serialized in DB
  createdAt: Date;
  updatedAt: Date;
  completedAt: Date | null;
}

/** Phase within a research project */
export interface ResearchPhase {
  id: PhaseId;
  projectId: ProjectId;
  workflowId: WorkflowId | null;
  name: string;
  description: string;
  order: number; // Execution order within project
  status: PhaseStatus;
  dependsOn: PhaseId[]; // Phase IDs this depends on
  config: PhaseConfig; // JSON-serialized in DB
  approvalRequired: boolean;
  approvedBy: string | null; // Human reviewer identifier
  approvedAt: Date | null;
  startedAt: Date | null;
  completedAt: Date | null;
  error: string | null; // Error message if failed
  retryCount: number;
  maxRetries: number;
  createdAt: Date;
  updatedAt: Date;
}

/** Evidence item — a sourced claim or data point */
export interface EvidenceItem {
  id: EvidenceId;
  projectId: ProjectId;
  phaseId: PhaseId;
  sourceType: "url" | "file" | "agent_output" | "manual";
  sourceUri: string | null; // URL, file path, or null for manual
  sourceTitle: string | null;
  sourceAuthor: string | null;
  sourceDate: Date | null;
  content: string; // The evidence content (markdown)
  summary: string | null; // AI-generated summary
  confidence: EvidenceConfidence;
  citations: string[]; // JSON-serialized citation strings
  tags: string[];
  embedding: Float32Array | null; // For vector similarity search (future)
  createdAt: Date;
}

/** Memory entry — system knowledge store */
export interface MemoryEntry {
  id: MemoryId;
  projectId: ProjectId;
  type: MemoryType;
  content: string; // Markdown content
  summary: string | null; // Compressed version for long-term
  source: string; // What produced this memory (agent, phase, manual)
  importance: number; // 0.0 - 1.0, drives retention
  accessCount: number; // How often retrieved
  lastAccessedAt: Date | null;
  expiresAt: Date | null; // For short-term memory TTL
  createdAt: Date;
  updatedAt: Date;
}

/** Agent session — records an AI model invocation */
export interface AgentSession {
  id: SessionId;
  projectId: ProjectId;
  phaseId: PhaseId;
  agentRole: AgentRole;
  agentName: string; // Specific agent identifier
  modelProvider: string; // "openai", "anthropic", "ollama"
  modelId: string; // "gpt-4o", "claude-sonnet-4-20250514", "llama3"
  prompt: string; // System + user prompt sent
  response: string | null; // Model response
  tokenInput: number;
  tokenOutput: number;
  costUsd: number | null; // Calculated cost
  latencyMs: number;
  status: "pending" | "running" | "completed" | "failed" | "timeout";
  error: string | null;
  metadata: Record<string, unknown>; // JSON-serialized, model-specific data
  createdAt: Date;
  completedAt: Date | null;
}

/** Workflow definition — DAG of tasks */
export interface WorkflowDefinition {
  id: WorkflowId;
  name: string;
  description: string;
  version: string; // SemVer
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  config: Record<string, unknown>; // JSON-serialized
  isBuiltin: boolean;
  createdAt: Date;
  updatedAt: Date;
}

/** Single node in a workflow DAG */
export interface WorkflowNode {
  id: string; // Unique within workflow
  type: "agent_task" | "human_review" | "checkpoint" | "condition" | "parallel";
  name: string;
  config: Record<string, unknown>; // Node-specific configuration
  timeout: number; // milliseconds
  retryPolicy: RetryPolicy;
}

/** Edge connecting workflow nodes */
export interface WorkflowEdge {
  from: string; // Source node ID
  to: string; // Target node ID
  condition: string | null; // Conditional expression
}

/** Retry policy for failed operations */
export interface RetryPolicy {
  maxRetries: number;
  backoffMs: number; // Initial backoff
  backoffMultiplier: number;
  maxBackoffMs: number;
}

/** Checkpoint — snapshot of project state for resume */
export interface Checkpoint {
  id: CheckpointId;
  projectId: ProjectId;
  phaseId: PhaseId;
  snapshot: ProjectSnapshot; // JSON-serialized full state
  memorySnapshot: MemorySnapshot;
  reason: "phase_start" | "phase_complete" | "manual" | "periodic";
  createdAt: Date;
}

/** Full project state snapshot */
export interface ProjectSnapshot {
  project: ResearchProject;
  phases: ResearchPhase[];
  evidence: EvidenceItem[];
  memorySummary: {
    shortTerm: number;
    longTerm: number;
    episodic: number;
  };
}

/** Memory snapshot for checkpoint */
export interface MemorySnapshot {
  shortTerm: MemoryEntry[];
  longTermCount: number;
  episodicCount: number;
}

/** Audit log entry */
export interface AuditEntry {
  id: AuditId;
  projectId: ProjectId;
  action: AuditAction;
  actor: string; // "system", "user", agent name
  entityType: "project" | "phase" | "evidence" | "memory" | "session" | "workflow";
  entityId: string;
  details: Record<string, unknown>; // JSON-serialized
  timestamp: Date;
}

// ─── Configuration Types ──────────────────────────────────────────────────────

/** Top-level system configuration */
export interface SystemConfig {
  dataDir: string;
  projectDir: string;
  logLevel: "debug" | "info" | "warn" | "error";
  database: DatabaseConfig;
  agents: AgentsConfig;
  storage: StorageConfig;
  plugins: PluginsConfig;
  http: HttpConfig;
}

/** Database configuration */
export interface DatabaseConfig {
  path: string;
  walMode: boolean;
  busyTimeout: number;
  journalMode: "delete" | "truncate" | "persist" | "memory" | "wal";
}

/** Agent/model configuration */
export interface AgentsConfig {
  defaultProvider: string;
  providers: Record<string, ProviderConfig>;
  defaults: AgentDefaults;
  timeouts: AgentTimeouts;
}

/** Provider configuration */
export interface ProviderConfig {
  apiKey: string | null; // Env var name or inline (never stored in config files)
  baseUrl: string | null; // For custom endpoints
  models: Record<string, ModelConfig>;
  rateLimit: RateLimitConfig;
}

/** Model configuration */
export interface ModelConfig {
  maxTokens: number;
  temperature: number;
  costPerInputToken: number;
  costPerOutputToken: number;
}

/** Rate limiting */
export interface RateLimitConfig {
  requestsPerMinute: number;
  tokensPerMinute: number;
}

/** Agent defaults */
export interface AgentDefaults {
  temperature: number;
  maxTokens: number;
  timeout: number; // ms
  retryPolicy: RetryPolicy;
}

/** Agent timeouts */
export interface AgentTimeouts {
  task: number; // Per-task timeout
  phase: number; // Per-phase timeout
  project: number; // Per-project timeout
}

/** Storage configuration */
export interface StorageConfig {
  artifactFormat: "markdown" | "json" | "both";
  gitEnabled: boolean;
  gitAutoCommit: boolean;
  checkpointInterval: number; // ms between auto-checkpoints
  maxArtifactSize: number; // bytes
}

/** Plugin configuration */
export interface PluginsConfig {
  enabled: boolean;
  directory: string;
  allowedModules: string[]; // NPM modules plugins can import
  sandbox: boolean;
}

/** HTTP API configuration */
export interface HttpConfig {
  enabled: boolean;
  port: number;
  host: string;
  cors: CorsConfig;
  rateLimit: RateLimitConfig;
}

/** CORS configuration */
export interface CorsConfig {
  enabled: boolean;
  origins: string[];
}

/** Per-project configuration */
export interface ProjectConfig {
  maxPhases: number;
  maxRetriesPerPhase: number;
  approvalGates: ApprovalGateConfig[];
  checkpointOnPhaseComplete: boolean;
  autoSaveInterval: number; // ms
}

/** Approval gate configuration */
export interface ApprovalGateConfig {
  phasePattern: string; // Glob pattern matching phase names
  required: boolean;
  approvers: string[];
  timeout: number; // ms, 0 = no timeout
}

/** Phase-specific configuration */
export interface PhaseConfig {
  agentRole: AgentRole;
  modelOverride: string | null; // Override default model
  temperatureOverride: number | null;
  maxTokensOverride: number | null;
  customInstructions: string | null;
  parallel: boolean; // Allow parallel task execution within phase
  checkpoint: boolean; // Save checkpoint before phase
}

// ─── Result Type ──────────────────────────────────────────────────────────────

export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

export function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

export function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

// ─── Event Types ──────────────────────────────────────────────────────────────

export type SystemEvent =
  | { type: "project.created"; projectId: ProjectId }
  | { type: "project.updated"; projectId: ProjectId; field: string }
  | { type: "phase.started"; projectId: ProjectId; phaseId: PhaseId }
  | { type: "phase.completed"; projectId: ProjectId; phaseId: PhaseId }
  | { type: "phase.failed"; projectId: ProjectId; phaseId: PhaseId; error: string }
  | { type: "phase.awaiting_approval"; projectId: ProjectId; phaseId: PhaseId }
  | { type: "phase.approved"; projectId: ProjectId; phaseId: PhaseId }
  | { type: "phase.rejected"; projectId: ProjectId; phaseId: PhaseId; reason: string }
  | { type: "evidence.collected"; projectId: ProjectId; evidenceId: EvidenceId }
  | { type: "memory.written"; projectId: ProjectId; memoryId: MemoryId; memType: MemoryType }
  | { type: "agent.invoked"; projectId: ProjectId; sessionId: SessionId }
  | { type: "agent.completed"; projectId: ProjectId; sessionId: SessionId }
  | { type: "agent.failed"; projectId: ProjectId; sessionId: SessionId; error: string }
  | { type: "checkpoint.saved"; projectId: ProjectId; checkpointId: CheckpointId }
  | { type: "checkpoint.restored"; projectId: ProjectId; checkpointId: CheckpointId }
  | { type: "system.error"; component: string; error: string };

export type EventHandler = (event: SystemEvent) => void | Promise<void>;
```

---

## 3. Database Schema — Drizzle ORM

```typescript
// src/db/schema/projects.ts

import { sqliteTable, text, integer, real } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const projects = sqliteTable("projects", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description").notNull().default(""),
  status: text("status").notNull().default("draft"),
  goal: text("goal").notNull(),
  hypothesis: text("hypothesis"),
  methodology: text("methodology"),
  tags: text("tags").notNull().default("[]"), // JSON array
  config: text("config").notNull().default("{}"), // JSON object
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
  completedAt: integer("completed_at", { mode: "timestamp" }),
});

// src/db/schema/phases.ts

export const phases = sqliteTable("phases", {
  id: text("id").primaryKey(),
  projectId: text("project_id")
    .notNull()
    .references(() => projects.id, { onDelete: "cascade" }),
  workflowId: text("workflow_id"),
  name: text("name").notNull(),
  description: text("description").notNull().default(""),
  order: integer("order").notNull(),
  status: text("status").notNull().default("pending"),
  dependsOn: text("depends_on").notNull().default("[]"), // JSON array of phase IDs
  config: text("config").notNull().default("{}"), // JSON
  approvalRequired: integer("approval_required", { mode: "boolean" }).notNull().default(false),
  approvedBy: text("approved_by"),
  approvedAt: integer("approved_at", { mode: "timestamp" }),
  startedAt: integer("started_at", { mode: "timestamp" }),
  completedAt: integer("completed_at", { mode: "timestamp" }),
  error: text("error"),
  retryCount: integer("retry_count").notNull().default(0),
  maxRetries: integer("max_retries").notNull().default(3),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

// src/db/schema/evidence.ts

export const evidence = sqliteTable("evidence", {
  id: text("id").primaryKey(),
  projectId: text("project_id")
    .notNull()
    .references(() => projects.id, { onDelete: "cascade" }),
  phaseId: text("phase_id")
    .notNull()
    .references(() => phases.id, { onDelete: "cascade" }),
  sourceType: text("source_type").notNull(), // url, file, agent_output, manual
  sourceUri: text("source_uri"),
  sourceTitle: text("source_title"),
  sourceAuthor: text("source_author"),
  sourceDate: integer("source_date", { mode: "timestamp" }),
  content: text("content").notNull(), // Markdown
  summary: text("summary"),
  confidence: text("confidence").notNull().default("medium"),
  citations: text("citations").notNull().default("[]"), // JSON array
  tags: text("tags").notNull().default("[]"), // JSON array
  embedding: blob("embedding"), // Float32Array for vector search (future)
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

// src/db/schema/memory.ts

export const memory = sqliteTable("memory", {
  id: text("id").primaryKey(),
  projectId: text("project_id")
    .notNull()
    .references(() => projects.id, { onDelete: "cascade" }),
  type: text("type").notNull(), // short_term, long_term, episodic
  content: text("content").notNull(), // Markdown
  summary: text("summary"),
  source: text("source").notNull(), // What produced this
  importance: real("importance").notNull().default(0.5),
  accessCount: integer("access_count").notNull().default(0),
  lastAccessedAt: integer("last_accessed_at", { mode: "timestamp" }),
  expiresAt: integer("expires_at", { mode: "timestamp" }),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

// src/db/schema/sessions.ts

export const sessions = sqliteTable("sessions", {
  id: text("id").primaryKey(),
  projectId: text("project_id")
    .notNull()
    .references(() => projects.id, { onDelete: "cascade" }),
  phaseId: text("phase_id")
    .notNull()
    .references(() => phases.id, { onDelete: "cascade" }),
  agentRole: text("agent_role").notNull(),
  agentName: text("agent_name").notNull(),
  modelProvider: text("model_provider").notNull(),
  modelId: text("model_id").notNull(),
  prompt: text("prompt").notNull(),
  response: text("response"),
  tokenInput: integer("token_input").notNull().default(0),
  tokenOutput: integer("token_output").notNull().default(0),
  costUsd: real("cost_usd"),
  latencyMs: integer("latency_ms").notNull().default(0),
  status: text("status").notNull().default("pending"),
  error: text("error"),
  metadata: text("metadata").notNull().default("{}"), // JSON
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
  completedAt: integer("completed_at", { mode: "timestamp" }),
});

// src/db/schema/workflows.ts

export const workflows = sqliteTable("workflows", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  description: text("description").notNull().default(""),
  version: text("version").notNull().default("1.0.0"),
  nodes: text("nodes").notNull().default("[]"), // JSON array of WorkflowNode
  edges: text("edges").notNull().default("[]"), // JSON array of WorkflowEdge
  config: text("config").notNull().default("{}"), // JSON
  isBuiltin: integer("is_builtin", { mode: "boolean" }).notNull().default(false),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

// src/db/schema/audit.ts

export const audit = sqliteTable("audit", {
  id: text("id").primaryKey(),
  projectId: text("project_id")
    .notNull()
    .references(() => projects.id, { onDelete: "cascade" }),
  action: text("action").notNull(),
  actor: text("actor").notNull().default("system"),
  entityType: text("entity_type").notNull(),
  entityId: text("entity_id").notNull(),
  details: text("details").notNull().default("{}"), // JSON
  timestamp: integer("timestamp", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

// Checkpoints table (add to schema/checkpoints.ts)
export const checkpoints = sqliteTable("checkpoints", {
  id: text("id").primaryKey(),
  projectId: text("project_id")
    .notNull()
    .references(() => projects.id, { onDelete: "cascade" }),
  phaseId: text("phase_id")
    .notNull()
    .references(() => phases.id, { onDelete: "cascade" }),
  snapshot: text("snapshot").notNull(), // JSON — full ProjectSnapshot
  memorySnapshot: text("memory_snapshot").notNull(), // JSON
  reason: text("reason").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

// Indexes for performance
// (these would be in a migration file)
/*
CREATE INDEX idx_phases_project_id ON phases(project_id);
CREATE INDEX idx_phases_status ON phases(status);
CREATE INDEX idx_evidence_project_id ON evidence(project_id);
CREATE INDEX idx_evidence_phase_id ON evidence(phase_id);
CREATE INDEX idx_evidence_confidence ON evidence(confidence);
CREATE INDEX idx_memory_project_id ON memory(project_id);
CREATE INDEX idx_memory_type ON memory(type);
CREATE INDEX idx_memory_importance ON memory(importance DESC);
CREATE INDEX idx_sessions_project_id ON sessions(project_id);
CREATE INDEX idx_sessions_phase_id ON sessions(phase_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_audit_project_id ON audit(project_id);
CREATE INDEX idx_audit_timestamp ON audit(timestamp DESC);
CREATE INDEX idx_audit_action ON audit(action);
CREATE INDEX idx_checkpoints_project_id ON checkpoints(project_id);
CREATE INDEX idx_checkpoints_phase_id ON checkpoints(phase_id);
*/
```

---

## 4. Storage Architecture

### 4.1 File System Layout

Each research project gets its own directory under `projects/`. All artifacts are Markdown files with YAML frontmatter for metadata. The file system is the source of truth for artifacts; the database indexes them.

```
projects/{project-id}/
├── project.md                            # YAML frontmatter + Markdown body
├── phases/
│   └── {phase-id}/
│       ├── phase.md                      # Phase definition + status
│       ├── artifacts/
│       │   ├── {timestamp}-{name}.md     # Timestamped artifact files
│       │   └── ...
│       └── evidence/
│           ├── {evidence-id}.md          # One file per evidence item
│           └── ...
├── memory/
│   ├── short-term.md                     # Current working context (single file, overwritten)
│   ├── long-term/
│   │   ├── {topic-slug}.md              # One file per topic cluster
│   │   └── ...
│   └── episodic/
│       └── log.md                       # Append-only chronological log
└── checkpoints/
    ├── {checkpoint-id}.json             # Serialized checkpoint
    └── ...
```

### 4.2 Markdown Artifact Format

```markdown
---
id: "evt-abc123"
projectId: "proj-xyz789"
phaseId: "phase-def456"
sourceType: "agent_output"
sourceUri: null
confidence: "high"
citations:
  - "Smith et al. 2024"
  - "https://arxiv.org/abs/2024.12345"
tags:
  - "machine-learning"
  - "neuroscience"
createdAt: "2026-07-30T14:30:00Z"
---

# Evidence: Neural Correlates of Decision Making

## Summary

fMRI studies consistently show activation in the ventromedial prefrontal
cortex during value-based decision making...

## Source Details

Original study conducted at MIT with n=120 participants...

## Confidence Assessment

High confidence based on:
- Multiple replications across labs
- Large sample sizes (n > 100)
- Consistent effect sizes (d > 0.8)
```

### 4.3 Git Integration Strategy

```typescript
// src/storage/git-store.ts

export interface GitStore {
  /** Initialize git repo for a project */
  initProject(projectId: ProjectId): Promise<void>;

  /** Stage and commit all changes in project directory */
  commit(
    projectId: ProjectId,
    message: string,
    files?: string[]
  ): Promise<string>; // Returns commit hash

  /** Get diff between two commits */
  diff(projectId: ProjectId, from: string, to: string): Promise<string>;

  /** Get log of commits */
  log(projectId: ProjectId, limit?: number): Promise<GitCommit[]>;

  /** Restore project to a specific commit */
  checkout(projectId: ProjectId, commitHash: string): Promise<void>;

  /** Check if working directory is clean */
  isClean(projectId: ProjectId): Promise<boolean>;
}

export interface GitCommit {
  hash: string;
  message: string;
  author: string;
  date: Date;
}
```

**Git Strategy:**
- Each project gets its own git repository (not submodules) for isolation
- Auto-commit on: phase completion, checkpoint save, manual save
- Commit messages follow conventional commits: `feat(phase): complete literature review`
- Tags for major milestones: `v1.0-phase-1-complete`
- `.gitignore` in each project excludes: `*.tmp`, `*.log`, `node_modules/`

### 4.4 SQLite Configuration

```typescript
// src/db/connection.ts

import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

export function createDatabase(dbPath: string): ReturnType<typeof drizzle> {
  const sqlite = new Database(dbPath);

  // Performance and safety pragmas
  sqlite.pragma("journal_mode = WAL"); // Write-ahead logging for concurrent reads
  sqlite.pragma("busy_timeout = 5000"); // 5s timeout on locks
  sqlite.pragma("synchronous = NORMAL"); // Good durability, better performance
  sqlite.pragma("foreign_keys = ON");
  sqlite.pragma("cache_size = -8000"); // 8MB cache
  sqlite.pragma("wal_autocheckpoint = 1000"); // Checkpoint every 1000 pages

  return drizzle(sqlite, { schema });
}
```

---

## 5. API Design — Internal Module APIs

### 5.1 Project Service

```typescript
// src/core/project-service.ts

import { ResearchProject, ProjectId, PhaseId, Result } from "../core/types";

export interface ProjectService {
  /** Create a new research project */
  create(input: CreateProjectInput): Promise<Result<ResearchProject>>;

  /** Get project by ID */
  get(id: ProjectId): Promise<Result<ResearchProject | null>>;

  /** List all projects with optional filters */
  list(filter?: ProjectFilter): Promise<Result<ResearchProject[]>>;

  /** Update project fields */
  update(
    id: ProjectId,
    input: UpdateProjectInput
  ): Promise<Result<ResearchProject>>;

  /** Delete project and all associated data */
  delete(id: ProjectId): Promise<Result<void>>;

  /** Get project with all phases */
  getWithPhases(
    id: ProjectId
  ): Promise<Result<{ project: ResearchProject; phases: Phase[] }>>;

  /** Archive a completed project */
  archive(id: ProjectId): Promise<Result<ResearchProject>>;
}

export interface CreateProjectInput {
  name: string;
  description: string;
  goal: string;
  hypothesis?: string;
  methodology?: string;
  tags?: string[];
  config?: Partial<ProjectConfig>;
}

export interface UpdateProjectInput {
  name?: string;
  description?: string;
  status?: ProjectStatus;
  goal?: string;
  hypothesis?: string;
  methodology?: string;
  tags?: string[];
}

export interface ProjectFilter {
  status?: ProjectStatus[];
  tags?: string[];
  search?: string; // Full-text search on name, description, goal
  limit?: number;
  offset?: number;
  sortBy?: "createdAt" | "updatedAt" | "name";
  sortOrder?: "asc" | "desc";
}
```

### 5.2 Phase Service

```typescript
// src/core/phase-service.ts

import {
  PhaseId,
  ProjectId,
  ResearchPhase,
  PhaseStatus,
  Result,
} from "../core/types";

export interface PhaseService {
  /** Create a new phase in a project */
  create(projectId: ProjectId, input: CreatePhaseInput): Promise<Result<ResearchPhase>>;

  /** Get phase by ID */
  get(id: PhaseId): Promise<Result<ResearchPhase | null>>;

  /** List phases for a project */
  listByProject(projectId: ProjectId): Promise<Result<ResearchPhase[]>>;

  /** Update phase status */
  updateStatus(
    id: PhaseId,
    status: PhaseStatus,
    error?: string
  ): Promise<Result<ResearchPhase>>;

  /** Mark phase as awaiting approval */
  requestApproval(id: PhaseId): Promise<Result<ResearchPhase>>;

  /** Approve a phase */
  approve(id: PhaseId, approver: string): Promise<Result<ResearchPhase>>;

  /** Reject a phase with reason */
  reject(
    id: PhaseId,
    approver: string,
    reason: string
  ): Promise<Result<ResearchPhase>>;

  /** Get phases ready to execute (dependencies met) */
  getReadyPhases(projectId: ProjectId): Promise<Result<ResearchPhase[]>>;

  /** Get phase execution history */
  getHistory(id: PhaseId): Promise<Result<PhaseHistoryEntry[]>>;
}

export interface CreatePhaseInput {
  name: string;
  description: string;
  workflowId?: string;
  order?: number;
  dependsOn?: PhaseId[];
  approvalRequired?: boolean;
  maxRetries?: number;
  config?: Partial<PhaseConfig>;
}

export interface PhaseHistoryEntry {
  action: string;
  actor: string;
  timestamp: Date;
  details: Record<string, unknown>;
}
```

### 5.3 Evidence Service

```typescript
// src/core/evidence-service.ts

import {
  EvidenceId,
  EvidenceItem,
  EvidenceConfidence,
  ProjectId,
  PhaseId,
  Result,
} from "../core/types";

export interface EvidenceService {
  /** Collect a new evidence item */
  collect(input: CollectEvidenceInput): Promise<Result<EvidenceItem>>;

  /** Get evidence by ID */
  get(id: EvidenceId): Promise<Result<EvidenceItem | null>>;

  /** List evidence for a project */
  listByProject(
    projectId: ProjectId,
    filter?: EvidenceFilter
  ): Promise<Result<EvidenceItem[]>>;

  /** List evidence for a phase */
  listByPhase(phaseId: PhaseId): Promise<Result<EvidenceItem[]>>;

  /** Update evidence confidence or content */
  update(
    id: EvidenceId,
    input: UpdateEvidenceInput
  ): Promise<Result<EvidenceItem>>;

  /** Delete evidence */
  delete(id: EvidenceId): Promise<Result<void>>;

  /** Search evidence by content */
  search(
    projectId: ProjectId,
    query: string
  ): Promise<Result<EvidenceItem[]>>;

  /** Get citation in specified format */
  getCitation(
    id: EvidenceId,
    format: "apa" | "mla" | "chicago" | "bibtex"
  ): Promise<Result<string>>;

  /** Export all evidence as formatted document */
  exportAll(
    projectId: ProjectId,
    format: "markdown" | "json" | "csv"
  ): Promise<Result<string>>;
}

export interface CollectEvidenceInput {
  projectId: ProjectId;
  phaseId: PhaseId;
  sourceType: "url" | "file" | "agent_output" | "manual";
  sourceUri?: string;
  sourceTitle?: string;
  sourceAuthor?: string;
  sourceDate?: Date;
  content: string;
  summary?: string;
  confidence: EvidenceConfidence;
  citations?: string[];
  tags?: string[];
}

export interface UpdateEvidenceInput {
  content?: string;
  summary?: string;
  confidence?: EvidenceConfidence;
  citations?: string[];
  tags?: string[];
}

export interface EvidenceFilter {
  confidence?: EvidenceConfidence[];
  sourceType?: string[];
  tags?: string[];
  search?: string;
  limit?: number;
  offset?: number;
}
```

### 5.4 Memory Service

```typescript
// src/core/memory-service.ts

import {
  MemoryId,
  MemoryEntry,
  MemoryType,
  ProjectId,
  Result,
} from "../core/types";

export interface MemoryService {
  /** Write a new memory entry */
  write(input: WriteMemoryInput): Promise<Result<MemoryEntry>>;

  /** Read a memory entry (increments access count) */
  get(id: MemoryId): Promise<Result<MemoryEntry | null>>;

  /** Search memories by content similarity */
  search(
    projectId: ProjectId,
    query: string,
    options?: MemorySearchOptions
  ): Promise<Result<MemoryEntry[]>>;

  /** List memories by type */
  listByType(
    projectId: ProjectId,
    type: MemoryType
  ): Promise<Result<MemoryEntry[]>>;

  /** Update memory content or importance */
  update(
    id: MemoryId,
    input: UpdateMemoryInput
  ): Promise<Result<MemoryEntry>>;

  /** Delete expired short-term memories */
  gcExpired(projectId: ProjectId): Promise<Result<number>>;

  /** Compress short-term memories into long-term summaries */
  consolidate(projectId: ProjectId): Promise<Result<MemoryEntry[]>>;

  /** Get memory summary for a project */
  getSummary(projectId: ProjectId): Promise<Result<MemorySummary>>;

  /** Clear short-term memory for a project */
  clearShortTerm(projectId: ProjectId): Promise<Result<void>>;
}

export interface WriteMemoryInput {
  projectId: ProjectId;
  type: MemoryType;
  content: string;
  source: string;
  importance?: number;
  expiresAt?: Date;
}

export interface UpdateMemoryInput {
  content?: string;
  summary?: string;
  importance?: number;
}

export interface MemorySearchOptions {
  type?: MemoryType;
  minImportance?: number;
  limit?: number;
  maxAge?: number; // ms since creation
}

export interface MemorySummary {
  shortTermCount: number;
  longTermCount: number;
  episodicCount: number;
  totalSizeBytes: number;
  oldestEntry: Date | null;
  newestEntry: Date | null;
}
```

### 5.5 Agent Orchestrator

```typescript
// src/agents/orchestrator.ts

import {
  PhaseId,
  ProjectId,
  AgentRole,
  SessionId,
  Result,
} from "../core/types";

export interface AgentOrchestrator {
  /** Execute a phase using configured agents */
  executePhase(
    projectId: ProjectId,
    phaseId: PhaseId
  ): Promise<Result<PhaseExecutionResult>>;

  /** Execute a single task */
  executeTask(
    projectId: ProjectId,
    phaseId: PhaseId,
    input: TaskInput
  ): Promise<Result<TaskResult>>;

  /** Get execution status */
  getStatus(sessionId: SessionId): Promise<Result<SessionStatus>>;

  /** Cancel a running execution */
  cancel(sessionId: SessionId): Promise<Result<void>>;

  /** Get token usage and cost summary */
  getUsage(
    projectId: ProjectId
  ): Promise<Result<UsageSummary>>;
}

export interface TaskInput {
  role: AgentRole;
  prompt: string;
  context?: string; // Additional context from memory/evidence
  modelOverride?: string;
  temperature?: number;
  maxTokens?: number;
}

export interface TaskResult {
  sessionId: SessionId;
  response: string;
  tokenInput: number;
  tokenOutput: number;
  costUsd: number | null;
  latencyMs: number;
  evidenceCollected: number; // Count of evidence items produced
  memoryWritten: number; // Count of memory entries produced
}

export interface PhaseExecutionResult {
  phaseId: PhaseId;
  tasksCompleted: number;
  evidenceCollected: number;
  memoryWritten: number;
  totalCostUsd: number;
  totalLatencyMs: number;
  output: string; // Phase output summary
}

export interface SessionStatus {
  sessionId: SessionId;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  progress?: number; // 0-100
  currentTask?: string;
}

export interface UsageSummary {
  totalSessions: number;
  totalTokenInput: number;
  totalTokenOutput: number;
  totalCostUsd: number;
  byProvider: Record<
    string,
    {
      sessions: number;
      tokenInput: number;
      tokenOutput: number;
      costUsd: number;
    }
  >;
  byPhase: Record<
    string,
    {
      sessions: number;
      costUsd: number;
    }
  >;
}
```

### 5.6 Workflow Engine

```typescript
// src/workflow/engine.ts

import {
  WorkflowId,
  WorkflowDefinition,
  WorkflowNode,
  ProjectId,
  PhaseId,
  Result,
} from "../core/types";

export interface WorkflowEngine {
  /** Register a workflow definition */
  register(workflow: WorkflowDefinition): Promise<Result<void>>;

  /** Get workflow by ID */
  get(id: WorkflowId): Promise<Result<WorkflowDefinition | null>>;

  /** List all available workflows */
  list(): Promise<Result<WorkflowDefinition[]>>;

  /** Validate a workflow DAG (no cycles, all edges valid) */
  validate(workflow: WorkflowDefinition): Promise<Result<ValidationResult>>;

  /** Execute a workflow for a phase */
  execute(
    workflowId: WorkflowId,
    projectId: ProjectId,
    phaseId: PhaseId
  ): Promise<Result<WorkflowExecutionResult>>;

  /** Get current execution state */
  getState(
    projectId: ProjectId,
    phaseId: PhaseId
  ): Promise<Result<WorkflowState | null>>;

  /** Save checkpoint of workflow execution */
  saveCheckpoint(
    projectId: ProjectId,
    phaseId: PhaseId
  ): Promise<Result<CheckpointId>>;

  /** Restore workflow execution from checkpoint */
  restoreCheckpoint(
    checkpointId: CheckpointId
  ): Promise<Result<WorkflowState>>;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface WorkflowExecutionResult {
  completedNodes: string[];
  failedNodes: string[];
  output: Record<string, unknown>;
}

export interface WorkflowState {
  workflowId: WorkflowId;
  projectId: ProjectId;
  phaseId: PhaseId;
  completedNodes: Set<string>;
  currentNode: string | null;
  nodeStates: Record<string, NodeState>;
  startedAt: Date;
  updatedAt: Date;
}

export interface NodeState {
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  output?: unknown;
  error?: string;
  startedAt?: Date;
  completedAt?: Date;
}
```

### 5.7 Approval Service

```typescript
// src/approval/gate.ts

import {
  PhaseId,
  ProjectId,
  ResearchPhase,
  Result,
} from "../core/types";

export interface ApprovalService {
  /** Check if a phase requires approval */
  requiresApproval(phase: ResearchPhase): boolean;

  /** Request approval for a phase */
  requestApproval(
    phaseId: PhaseId,
    reason?: string
  ): Promise<Result<ApprovalRequest>>;

  /** Approve a phase */
  approve(
    phaseId: PhaseId,
    approver: string,
    comments?: string
  ): Promise<Result<ResearchPhase>>;

  /** Reject a phase */
  reject(
    phaseId: PhaseId,
    approver: string,
    reason: string
  ): Promise<Result<ResearchPhase>>;

  /** Get pending approval requests */
  getPending(
    projectId?: ProjectId
  ): Promise<Result<ApprovalRequest[]>>;

  /** Generate review artifact for human review */
  generateReview(
    phaseId: PhaseId
  ): Promise<Result<ReviewDocument>>;
}

export interface ApprovalRequest {
  phaseId: PhaseId;
  projectId: ProjectId;
  phaseName: string;
  reason: string;
  requestedAt: Date;
  timeout: number | null;
  approvers: string[];
}

export interface ReviewDocument {
  phaseId: PhaseId;
  phaseName: string;
  summary: string;
  artifacts: ArtifactSummary[];
  evidence: EvidenceSummary[];
  recommendations: string[];
  risks: string[];
}

export interface ArtifactSummary {
  name: string;
  path: string;
  preview: string; // First 500 chars
}

export interface EvidenceSummary {
  count: number;
  byConfidence: Record<string, number>;
  topSources: string[];
}
```

### 5.8 Plugin System

```typescript
// src/plugins/types.ts

import { Result } from "../core/types";

export interface ResearchOSPlugin {
  /** Plugin metadata */
  manifest: PluginManifest;

  /** Called when plugin is loaded */
  onLoad(context: PluginContext): Promise<Result<void>>;

  /** Called when plugin is unloaded */
  onUnload(): Promise<Result<void>>;

  /** Optional: provide custom agent roles */
  agentRoles?: AgentRoleProvider[];

  /** Optional: provide custom workflow templates */
  workflowTemplates?: WorkflowTemplate[];

  /** Optional: provide custom evidence validators */
  evidenceValidators?: EvidenceValidator[];
}

export interface PluginManifest {
  name: string;
  version: string;
  description: string;
  author: string;
  permissions: PluginPermission[];
}

export type PluginPermission =
  | "read:projects"
  | "write:projects"
  | "read:evidence"
  | "write:evidence"
  | "read:memory"
  | "write:memory"
  | "invoke:agents"
  | "read:config"
  | "write:config";

export interface PluginContext {
  projectService: any; // ProjectService
  evidenceService: any; // EvidenceService
  memoryService: any; // MemoryService
  logger: any; // Logger
  config: any; // SystemConfig
}

export interface AgentRoleProvider {
  role: string;
  execute(input: any): Promise<Result<any>>;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  nodes: any[];
  edges: any[];
}

export interface EvidenceValidator {
  name: string;
  validate(evidence: any): Promise<Result<{ valid: boolean; issues: string[] }>>;
}
```

---

## 6. CLI Interface

```typescript
// src/cli.ts

import { Command } from "commander";

const program = new Command();

program
  .name("researchos")
  .description("ResearchOS — AI-Powered Research Operating System")
  .version("0.1.0");

// ─── Project Commands ─────────────────────────────────────────────────────

program
  .command("project")
  .description("Manage research projects")
  .command("create")
  .argument("<name>", "Project name")
  .option("-g, --goal <goal>", "Research goal/question")
  .option("-d, --description <desc>", "Project description")
  .action(/* ... */);

program
  .command("project")
  .command("list")
  .option("-s, --status <status>", "Filter by status")
  .option("-t, --tag <tag>", "Filter by tag")
  .action(/* ... */);

program
  .command("project")
  .command("show <id>", "Show project details")
  .action(/* ... */);

// ─── Phase Commands ───────────────────────────────────────────────────────

program
  .command("phase")
  .description("Manage research phases")
  .command("add")
  .argument("<project-id>", "Parent project ID")
  .argument("<name>", "Phase name")
  .option("--workflow <id>", "Workflow template to use")
  .option("--depends-on <ids...>", "Phase dependencies")
  .action(/* ... */);

program
  .command("phase")
  .command("run <project-id> <phase-id>", "Execute a phase")
  .option("--dry-run", "Show what would be executed")
  .option("--model <model>", "Override model for this phase")
  .action(/* ... */);

program
  .command("phase")
  .command("approve <project-id> <phase-id>", "Approve a completed phase")
  .option("-m, --message <msg>", "Approval comments")
  .action(/* ... */);

// ─── Evidence Commands ────────────────────────────────────────────────────

program
  .command("evidence")
  .description("Manage research evidence")
  .command("add")
  .argument("<project-id>")
  .option("--phase <phase-id>")
  .option("--source <uri>", "Source URL or file path")
  .option("--confidence <level>", "high|medium|low|speculative")
  .action(/* ... */);

program
  .command("evidence")
  .command("list <project-id>", "List evidence for a project")
  .option("--confidence <level>", "Filter by confidence")
  .option("--format <fmt>", "markdown|json|csv")
  .action(/* ... */);

// ─── Memory Commands ──────────────────────────────────────────────────────

program
  .command("memory")
  .description("Manage research memory")
  .command("search <project-id> <query>", "Search memory")
  .option("--type <type>", "short_term|long_term|episodic")
  .option("--limit <n>", "Max results")
  .action(/* ... */);

program
  .command("memory")
  .command("consolidate <project-id>", "Compress short-term to long-term")
  .action(/* ... */);

// ─── Run Command (full project execution) ────────────────────────────────

program
  .command("run <project-id>", "Execute project phases in order")
  .option("--phase <phase-id>", "Run specific phase only")
  .option("--resume", "Resume from last checkpoint")
  .option("--dry-run", "Show execution plan without running")
  .action(/* ... */);

// ─── Status & Monitoring ─────────────────────────────────────────────────

program
  .command("status <project-id>", "Show project execution status")
  .action(/* ... */);

program
  .command("usage <project-id>", "Show token usage and costs")
  .action(/* ... */);

program
  .command("logs <project-id>", "Show project logs")
  .option("--phase <phase-id>", "Filter by phase")
  .option("--level <level>", "Log level filter")
  .option("--tail <n>", "Show last n entries")
  .action(/* ... */);

// ─── Config Commands ─────────────────────────────────────────────────────

program
  .command("config")
  .description("Manage configuration")
  .command("show", "Show current configuration")
  .action(/* ... */);

program
  .command("config")
  .command("set <key> <value>", "Set a config value")
  .action(/* ... */);

program
  .command("config")
  .command("validate", "Validate current configuration")
  .action(/* ... */);

// ─── Plugin Commands ─────────────────────────────────────────────────────

program
  .command("plugin")
  .description("Manage plugins")
  .command("list", "List installed plugins")
  .action(/* ... */);

program
  .command("plugin")
  .command("install <name>", "Install a plugin")
  .action(/* ... */);

program.parse();
```

---

## 7. Configuration System

### 7.1 Config Schema (Zod)

```typescript
// src/config/schema.ts

import { z } from "zod";

const RetryPolicySchema = z.object({
  maxRetries: z.number().int().min(0).max(10).default(3),
  backoffMs: z.number().int().min(100).default(1000),
  backoffMultiplier: z.number().min(1).max(10).default(2),
  maxBackoffMs: z.number().int().min(1000).default(30000),
});

const ModelConfigSchema = z.object({
  maxTokens: z.number().int().min(1).max(1000000).default(4096),
  temperature: z.number().min(0).max(2).default(0.7),
  costPerInputToken: z.number().min(0).default(0),
  costPerOutputToken: z.number().min(0).default(0),
});

const RateLimitConfigSchema = z.object({
  requestsPerMinute: z.number().int().min(1).default(60),
  tokensPerMinute: z.number().int().min(1000).default(100000),
});

const ProviderConfigSchema = z.object({
  apiKey: z.string().optional(),
  baseUrl: z.string().url().optional(),
  models: z.record(ModelConfigSchema).default({
    "default": {
      maxTokens: 4096,
      temperature: 0.7,
      costPerInputToken: 0,
      costPerOutputToken: 0,
    },
  }),
  rateLimit: RateLimitConfigSchema.default({}),
});

const AgentDefaultsSchema = z.object({
  temperature: z.number().min(0).max(2).default(0.7),
  maxTokens: z.number().int().min(1).default(4096),
  timeout: z.number().int().min(1000).default(120000),
  retryPolicy: RetryPolicySchema.default({}),
});

const AgentTimeoutsSchema = z.object({
  task: z.number().int().min(1000).default(300000), // 5 min
  phase: z.number().int().min(1000).default(3600000), // 1 hour
  project: z.number().int().min(1000).default(86400000), // 24 hours
});

const AgentsConfigSchema = z.object({
  defaultProvider: z.string().default("openai"),
  providers: z.record(ProviderConfigSchema).default({}),
  defaults: AgentDefaultsSchema.default({}),
  timeouts: AgentTimeoutsSchema.default({}),
});

const DatabaseConfigSchema = z.object({
  path: z.string().default("./data/researchos.db"),
  walMode: z.boolean().default(true),
  busyTimeout: z.number().int().min(100).default(5000),
  journalMode: z
    .enum(["delete", "truncate", "persist", "memory", "wal"])
    .default("wal"),
});

const StorageConfigSchema = z.object({
  artifactFormat: z.enum(["markdown", "json", "both"]).default("markdown"),
  gitEnabled: z.boolean().default(true),
  gitAutoCommit: z.boolean().default(true),
  checkpointInterval: z.number().int().min(0).default(300000), // 5 min
  maxArtifactSize: z.number().int().max(10485760).default(1048576), // 1MB
});

const PluginsConfigSchema = z.object({
  enabled: z.boolean().default(true),
  directory: z.string().default("./plugins"),
  allowedModules: z.array(z.string()).default([]),
  sandbox: z.boolean().default(true),
});

const CorsConfigSchema = z.object({
  enabled: z.boolean().default(false),
  origins: z.array(z.string()).default(["http://localhost:3000"]),
});

const HttpConfigSchema = z.object({
  enabled: z.boolean().default(false),
  port: z.number().int().min(1).max(65535).default(3456),
  host: z.string().default("127.0.0.1"),
  cors: CorsConfigSchema.default({}),
  rateLimit: RateLimitConfigSchema.default({
    requestsPerMinute: 120,
    tokensPerMinute: 1000000,
  }),
});

const ApprovalGateConfigSchema = z.object({
  phasePattern: z.string(),
  required: z.boolean().default(true),
  approvers: z.array(z.string()).default([]),
  timeout: z.number().int().min(0).default(0),
});

const ProjectConfigSchema = z.object({
  maxPhases: z.number().int().min(1).max(100).default(20),
  maxRetriesPerPhase: z.number().int().min(0).max(10).default(3),
  approvalGates: z.array(ApprovalGateConfigSchema).default([]),
  checkpointOnPhaseComplete: z.boolean().default(true),
  autoSaveInterval: z.number().int().min(0).default(60000), // 1 min
});

const PhaseConfigSchema = z.object({
  agentRole: z.enum(["planner", "researcher", "analyst", "reviewer", "custom"]).default("researcher"),
  modelOverride: z.string().nullable().default(null),
  temperatureOverride: z.number().min(0).max(2).nullable().default(null),
  maxTokensOverride: z.number().int().min(1).nullable().default(null),
  customInstructions: z.string().nullable().default(null),
  parallel: z.boolean().default(false),
  checkpoint: z.boolean().default(true),
});

export const SystemConfigSchema = z.object({
  dataDir: z.string().default("./data"),
  projectDir: z.string().default("./projects"),
  logLevel: z.enum(["debug", "info", "warn", "error"]).default("info"),
  database: DatabaseConfigSchema.default({}),
  agents: AgentsConfigSchema.default({}),
  storage: StorageConfigSchema.default({}),
  plugins: PluginsConfigSchema.default({}),
  http: HttpConfigSchema.default({}),
});

export type SystemConfigInput = z.input<typeof SystemConfigSchema>;
export type SystemConfigValidated = z.output<typeof SystemConfigSchema>;
```

### 7.2 Config Loader

```typescript
// src/config/loader.ts

import { SystemConfigSchema, SystemConfigValidated } from "./schema";
import { Result, ok, err } from "../core/types";

export interface ConfigLoader {
  /** Load config from file, env, and CLI args (merged in priority order) */
  load(cliArgs?: Record<string, unknown>): Promise<Result<SystemConfigValidated>>;

  /** Save config to file */
  save(config: SystemConfigValidated): Promise<Result<void>>;

  /** Get current validated config */
  get(): SystemConfigValidated;

  /** Watch for config changes */
  watch(handler: (config: SystemConfigValidated) => void): void;
}

// Config precedence (highest to lowest):
// 1. CLI arguments
// 2. Environment variables (RESEARCHOS_ prefix)
// 3. Project-level .researchos.json
// 4. User-level ~/.config/researchos/config.json
// 5. Built-in defaults

// Environment variable mapping:
// RESEARCHOS_DATA_DIR → dataDir
// RESEARCHOS_LOG_LEVEL → logLevel
// RESEARCHOS_DB_PATH → database.path
// RESEARCHOS_AGENT_DEFAULT_PROVIDER → agents.defaultProvider
// RESEARCHOS_HTTP_PORT → http.port
// RESEARCHOS_OPENAI_API_KEY → agents.providers.openai.apiKey
// RESEARCHOS_ANTHROPIC_API_KEY → agents.providers.anthropic.apiKey
```

### 7.3 Example Configuration File

```json
// .researchos.json (project-level)
{
  "logLevel": "info",
  "database": {
    "path": "./data/researchos.db",
    "walMode": true
  },
  "agents": {
    "defaultProvider": "openai",
    "providers": {
      "openai": {
        "models": {
          "gpt-4o": {
            "maxTokens": 16384,
            "temperature": 0.7,
            "costPerInputToken": 0.0025,
            "costPerOutputToken": 0.01
          }
        },
        "rateLimit": {
          "requestsPerMinute": 500,
          "tokensPerMinute": 800000
        }
      },
      "anthropic": {
        "models": {
          "claude-sonnet-4-20250514": {
            "maxTokens": 8192,
            "temperature": 0.7,
            "costPerInputToken": 0.003,
            "costPerOutputToken": 0.015
          }
        }
      },
      "ollama": {
        "baseUrl": "http://localhost:11434",
        "models": {
          "llama3": {
            "maxTokens": 4096,
            "temperature": 0.7,
            "costPerInputToken": 0,
            "costPerOutputToken": 0
          }
        }
      }
    },
    "defaults": {
      "temperature": 0.7,
      "maxTokens": 4096,
      "timeout": 120000,
      "retryPolicy": {
        "maxRetries": 3,
        "backoffMs": 1000,
        "backoffMultiplier": 2,
        "maxBackoffMs": 30000
      }
    }
  },
  "storage": {
    "gitEnabled": true,
    "gitAutoCommit": true,
    "checkpointInterval": 300000
  }
}
```

---

## 8. Module Responsibilities

### Module Map

| Module | Single Responsibility | Public Interface | Dependencies |
|--------|----------------------|------------------|--------------|
| `core/` | Shared types, errors, utilities | Types, Result, events, IDs | None |
| `db/` | Database access, schema, migrations | CRUD operations, connection | `core/` |
| `storage/` | File system artifacts, Git versioning | Artifact read/write, Git ops | `core/`, `config/` |
| `memory/` | Memory management, retrieval, consolidation | Write/search/consolidate | `core/`, `db/`, `storage/` |
| `agents/` | AI model orchestration, execution | Execute tasks, manage sessions | `core/`, `db/`, `config/`, `memory/` |
| `workflow/` | DAG validation, execution, scheduling | Register/execute/validate | `core/`, `db/`, `agents/` |
| `approval/` | Human-in-the-loop gates | Request/approve/reject | `core/`, `db/`, `storage/` |
| `evidence/` | Evidence collection, validation, citation | Collect/search/export | `core/`, `db/`, `storage/` |
| `plugins/` | Plugin loading, sandboxing | Load/unload, permissions | `core/`, `config/` |
| `config/` | Configuration loading, validation | Load/save/validate | `core/` |
| `http/` | HTTP API, WebSocket, middleware | Routes, middleware | All modules |

### Module Descriptions

**`core/`** — Foundation layer. Zero dependencies on other modules. Contains:
- `types.ts` — All TypeScript interfaces and branded types
- `errors.ts` — Custom error hierarchy (ConfigError, DatabaseError, AgentError, etc.)
- `result.ts` — Result<T, E> monad for error handling without exceptions
- `events.ts` — Typed event bus for inter-module communication
- `clock.ts` — Abstract clock interface for deterministic testing
- `id.ts` — UUID v4 generation with deterministic mode for tests
- `logger.ts` — Pino logger factory with structured fields

**`db/`** — Data persistence layer. SQLite via Drizzle ORM. Single responsibility: translate domain objects to/from database rows. Handles:
- Connection management with WAL mode
- Schema migrations (expand-and-contract)
- Transaction support for atomic operations
- Connection pooling (not needed for SQLite, but interface supports future migration)

**`storage/`** — File system operations. Responsible for:
- Creating/reading/writing Markdown artifact files with YAML frontmatter
- Git operations (commit, diff, log, checkout)
- Path resolution (project → phase → artifact)
- File locking for concurrent access
- Artifact validation (size limits, format checks)

**`memory/`** — Knowledge management. Three memory types:
- Short-term: Working memory for current phase, auto-expires, high importance
- Long-term: Persistent knowledge, compressed summaries, topic-indexed
- Episodic: Chronological event log, append-only, full detail
- Consolidation: Periodically compress short-term → long-term
- Retrieval: Search across all memory types with relevance scoring

**`agents/`** — AI orchestration. Components:
- `orchestrator.ts` — Coordinates phase execution, manages agent lifecycle
- `executor.ts` — Runs single agent tasks with prompt construction
- `pool.ts` — Manages concurrent agent execution (worker threads)
- `registry.ts` — Registers available agent types
- `models/` — Provider adapters (OpenAI, Anthropic, Ollama, fallback)
- `prompts/` — Markdown prompt templates with variable interpolation

**`workflow/`** — DAG-based execution engine. Handles:
- Workflow definition registration and validation
- Topological sort for execution ordering
- Parallel execution of independent nodes
- Checkpoint/resume for long-running workflows
- Built-in templates (literature review, experiment, meta-analysis)

**`approval/`** — Human gate system. Handles:
- Checking if approval is required (pattern matching on phase config)
- Generating review documents (summary, evidence, risks)
- Tracking approval decisions with audit trail
- Timeout handling for expired approval requests

**`evidence/`** — Research artifact management. Handles:
- Collecting evidence from agents, URLs, files, manual input
- Citation formatting (APA, MLA, Chicago, BibTeX)
- Confidence scoring with quality validation
- Search and retrieval with filtering
- Export in multiple formats

**`plugins/`** — Extension system. Handles:
- Dynamic plugin loading from `plugins/` directory
- Sandboxed execution (restricted file system, network, module access)
- Permission-based access control
- Plugin lifecycle (load, unload, health check)

**`config/`** — Configuration management. Handles:
- Multi-source config merging (defaults → file → env → CLI)
- Zod schema validation
- Hot-reload with file watching
- Type-safe config access throughout the system

**`http/`** — Optional API layer. Handles:
- REST endpoints for dashboard/UI integration
- WebSocket for real-time status updates
- OpenAPI spec generation
- Rate limiting, CORS, request ID middleware
- Authentication (API key for programmatic access)

---

## 9. Module Dependency Graph

```
                    ┌─────────┐
                    │  core/  │  ← Foundation (zero deps)
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
          ┌──────┐  ┌────────┐  ┌────────┐
          │ db/  │  │config/ │  │storage/│
          └──┬───┘  └────┬───┘  └───┬────┘
             │           │          │
             │     ┌─────┘          │
             │     │                │
             ▼     ▼                ▼
          ┌────────────┐     ┌──────────┐
          │  memory/   │     │ approval/│
          └─────┬──────┘     └────┬─────┘
                │                 │
                ▼                 │
          ┌──────────┐           │
          │ evidence/│◄──────────┘
          └─────┬────┘
                │
                ▼
          ┌──────────┐
          │ agents/  │
          └─────┬────┘
                │
                ▼
          ┌──────────┐
          │workflow/ │
          └─────┬────┘
                │
       ┌────────┼────────┐
       │        │        │
       ▼        ▼        ▼
  ┌────────┐ ┌───────┐ ┌──────┐
  │plugins/│ │ http/ │ │ cli  │
  └────────┘ └───────┘ └──────┘
```

**Dependency Rules:**
1. `core/` depends on nothing — it is the foundation
2. `db/`, `config/`, `storage/` depend only on `core/`
3. `memory/`, `approval/` depend on `core/`, `db/`, `storage/`
4. `evidence/` depends on `core/`, `db/`, `storage/`, `approval/`
5. `agents/` depends on `core/`, `db/`, `config/`, `memory/`
6. `workflow/` depends on `core/`, `db/`, `agents/`
7. `plugins/`, `http/`, `cli` are leaf nodes that depend on everything above

---

## 10. Error Handling Strategy

### 10.1 Error Hierarchy

```typescript
// src/core/errors.ts

export abstract class ResearchOSError extends Error {
  abstract readonly code: string;
  abstract readonly recoverable: boolean;
  readonly timestamp: Date;
  readonly context: Record<string, unknown>;

  constructor(
    message: string,
    context: Record<string, unknown> = {},
    cause?: Error
  ) {
    super(message, { cause });
    this.name = this.constructor.name;
    this.timestamp = new Date();
    this.context = context;
  }

  toJSON(): Record<string, unknown> {
    return {
      code: this.code,
      message: this.message,
      recoverable: this.recoverable,
      timestamp: this.timestamp.toISOString(),
      context: this.context,
      stack: this.stack,
    };
  }
}

// Configuration Errors (non-recoverable)
export class ConfigError extends ResearchOSError {
  readonly code = "CONFIG_ERROR";
  readonly recoverable = false;
}

// Database Errors (usually recoverable)
export class DatabaseError extends ResearchOSError {
  readonly code = "DATABASE_ERROR";
  readonly recoverable = true;
}

export class DatabaseLockError extends DatabaseError {
  readonly code = "DATABASE_LOCK_ERROR";
  readonly recoverable = true;
}

// Agent Errors (recoverable with retry)
export class AgentError extends ResearchOSError {
  readonly code = "AGENT_ERROR";
  readonly recoverable = true;
}

export class AgentTimeoutError extends AgentError {
  readonly code = "AGENT_TIMEOUT";
  readonly recoverable = true;
}

export class AgentRateLimitError extends AgentError {
  readonly code = "AGENT_RATE_LIMIT";
  readonly recoverable = true;
  readonly retryAfterMs: number;

  constructor(retryAfterMs: number, context: Record<string, unknown> = {}) {
    super(`Rate limited, retry after ${retryAfterMs}ms`, context);
    this.retryAfterMs = retryAfterMs;
  }
}

export class AgentAuthError extends AgentError {
  readonly code = "AGENT_AUTH_ERROR";
  readonly recoverable = false; // Can't fix bad API key
}

// Storage Errors (recoverable)
export class StorageError extends ResearchOSError {
  readonly code = "STORAGE_ERROR";
  readonly recoverable = true;
}

export class GitError extends StorageError {
  readonly code = "GIT_ERROR";
  readonly recoverable = true;
}

// Workflow Errors
export class WorkflowError extends ResearchOSError {
  readonly code = "WORKFLOW_ERROR";
  readonly recoverable = false;
}

export class ValidationError extends ResearchOSError {
  readonly code = "VALIDATION_ERROR";
  readonly recoverable = false;
}

// Plugin Errors
export class PluginError extends ResearchOSError {
  readonly code = "PLUGIN_ERROR";
  readonly recoverable = false;
}
```

### 10.2 Retry Logic

```typescript
// src/core/retry.ts

import { Result, ok, err } from "./types";
import { AgentError, AgentTimeoutError, AgentRateLimitError } from "./errors";

export interface RetryConfig {
  maxRetries: number;
  backoffMs: number;
  backoffMultiplier: number;
  maxBackoffMs: number;
  retryableErrors?: string[]; // Error codes to retry
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  config: RetryConfig,
  operationName: string
): Promise<T> {
  let lastError: Error | undefined;
  let delay = config.backoffMs;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      // Check if error is retryable
      if (error instanceof AgentRateLimitError) {
        delay = error.retryAfterMs;
      } else if (error instanceof AgentTimeoutError) {
        delay = Math.min(delay * config.backoffMultiplier, config.maxBackoffMs);
      } else if (error instanceof AgentError) {
        if (config.retryableErrors && !config.retryableErrors.includes(error.code)) {
          throw error; // Non-retryable agent error
        }
        delay = Math.min(delay * config.backoffMultiplier, config.maxBackoffMs);
      } else {
        throw error; // Unknown error, don't retry
      }

      if (attempt < config.maxRetries) {
        console.warn(
          `[retry] ${operationName} failed (attempt ${attempt + 1}/${config.maxRetries + 1}), retrying in ${delay}ms`,
          { error: error.message, code: (error as any).code }
        );
        await sleep(delay);
      }
    }
  }

  throw lastError;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
```

### 10.3 Circuit Breaker

```typescript
// src/agents/circuit-breaker.ts

export interface CircuitBreakerConfig {
  failureThreshold: number; // Failures before opening
  resetTimeout: number; // ms before half-open
  monitoringPeriod: number; // ms to count failures
}

export enum CircuitState {
  CLOSED = "closed", // Normal operation
  OPEN = "open", // Failing, reject requests
  HALF_OPEN = "half_open", // Testing if recovered
}

export class CircuitBreaker {
  private state = CircuitState.CLOSED;
  private failureCount = 0;
  private lastFailureTime = 0;
  private nextAttempt = 0;

  constructor(private config: CircuitBreakerConfig) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() > this.nextAttempt) {
        this.state = CircuitState.HALF_OPEN;
      } else {
        throw new Error(`Circuit breaker OPEN for ${this.config.resetTimeout}ms`);
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    this.state = CircuitState.CLOSED;
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.failureCount >= this.config.failureThreshold) {
      this.state = CircuitState.OPEN;
      this.nextAttempt = Date.now() + this.config.resetTimeout;
    }
  }

  getState(): CircuitState {
    return this.state;
  }

  reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
  }
}
```

### 10.4 Error Propagation Rules

1. **Agent errors** → Retry with backoff → Circuit breaker → Mark phase failed → Audit log
2. **Database errors** → Retry once → Log warning → Propagate as DatabaseError
3. **Storage errors** → Retry once → Log warning → Propagate as StorageError
4. **Config errors** → No retry → Log error → Exit process
5. **Plugin errors** → Log warning → Disable plugin → Continue without plugin
6. **All errors** → Structured log with context → Audit trail entry

---

## 11. Observability

### 11.1 Structured Logging

```typescript
// src/core/logger.ts

import pino from "pino";

export interface LogContext {
  projectId?: string;
  phaseId?: string;
  sessionId?: string;
  agentRole?: string;
  requestId?: string;
  userId?: string;
}

export function createLogger(
  level: string,
  baseContext?: LogContext
): pino.Logger {
  return pino({
    level,
    formatters: {
      level(label) {
        return { level: label };
      },
    },
    timestamp: pino.stdTimeFunctions.isoTime,
    serializers: {
      err: pino.stdSerializers.err,
      req: pino.stdSerializers.req,
      res: pino.stdSerializers.res,
    },
  }).child(baseContext ?? {});
}

// Usage:
// const log = createLogger("info", { projectId: "abc-123" });
// log.info({ phaseId: "phase-1", duration: 1500 }, "Phase completed");
// log.error({ err, sessionId: "sess-456" }, "Agent execution failed");
```

### 11.2 Metrics Collection

```typescript
// src/core/metrics.ts

export interface MetricsCollector {
  /** Record a counter (monotonically increasing) */
  increment(name: string, tags?: Record<string, string>): void;

  /** Record a gauge (point-in-time value) */
  gauge(name: string, value: number, tags?: Record<string, string>): void;

  /** Record a histogram (distribution of values) */
  histogram(name: string, value: number, tags?: Record<string, string>): void;

  /** Get current metrics snapshot */
  snapshot(): MetricsSnapshot;
}

export interface MetricsSnapshot {
  counters: Record<string, number>;
  gauges: Record<string, number>;
  histograms: Record<string, { min: number; max: number; avg: number; count: number }>;
}

// Key metrics to track:
// - agent.execution.count (counter, tags: provider, model, role)
// - agent.execution.duration (histogram, tags: provider, model)
// - agent.execution.tokens.input (counter, tags: provider, model)
// - agent.execution.tokens.output (counter, tags: provider, model)
// - agent.execution.cost (counter, tags: provider, model)
// - agent.execution.errors (counter, tags: provider, error_code)
// - phase.execution.count (counter, tags: status)
// - phase.execution.duration (histogram)
// - evidence.collected.count (counter, tags: source_type, confidence)
// - memory.written.count (counter, tags: memory_type)
// - memory.consolidation.duration (histogram)
// - checkpoint.save.count (counter)
// - checkpoint.restore.count (counter)
// - project.count (gauge, tags: status)
// - circuit_breaker.state (gauge, tags: provider)
// - db.query.duration (histogram, tags: operation)
// - http.request.duration (histogram, tags: method, path, status)
```

### 11.3 Tracing

```typescript
// src/core/tracing.ts

export interface TraceSpan {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  name: string;
  startTime: Date;
  endTime?: Date;
  status: "ok" | "error";
  attributes: Record<string, string>;
  events: TraceEvent[];
}

export interface TraceEvent {
  name: string;
  timestamp: Date;
  attributes: Record<string, string>;
}

// Trace a full phase execution:
// traceId: project-{projectId}-phase-{phaseId}-{timestamp}
// Spans:
//   - phase.execute (parent)
//     - agent.prepare_context
//     - memory.search
//     - agent.execute (child)
//       - model.call (external)
//     - evidence.collect
//     - memory.write
//     - checkpoint.save
```

### 11.4 Health Check

```typescript
// src/http/routes/health.ts

export interface HealthCheck {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: Date;
  checks: {
    database: { status: "ok" | "error"; latencyMs: number };
    storage: { status: "ok" | "error"; available: boolean };
    git: { status: "ok" | "error"; available: boolean };
    agents: { status: "ok" | "error"; providers: Record<string, boolean> };
  };
  version: string;
  uptime: number;
}
```

---

## 12. Security Boundaries

### 12.1 API Key Management

```typescript
// src/config/secrets.ts

export interface SecretManager {
  /** Get a secret value (API key, token, etc.) */
  get(key: string): Promise<string | null>;

  /** Set a secret value */
  set(key: string, value: string): Promise<void>;

  /** Delete a secret */
  delete(key: string): Promise<void>;

  /** List available secrets (names only, never values) */
  list(): Promise<string[]>;
}

// Secret resolution order:
// 1. Environment variable (RESEARCHOS_SECRET_<name>)
// 2. OS keychain (via keytar)
// 3. Encrypted file (~/.config/researchos/secrets.enc)
// 4. .env file (dev only, never committed)
//
// Rules:
// - API keys NEVER stored in researchos.json config files
// - .env files in .gitignore
// - Secrets encrypted at rest
// - Minimum privilege: each provider only gets its own key
```

### 12.2 Sandboxing

```typescript
// src/plugins/sandbox.ts

export interface PluginSandbox {
  /** Create an isolated execution context for a plugin */
  createContext(plugin: ResearchOSPlugin): PluginExecutionContext;

  /** Restrict file system access */
  restrictFileSystem(allowedPaths: string[]): void;

  /** Restrict network access */
  restrictNetwork(allowedDomains: string[]): void;

  /** Restrict module imports */
  restrictModules(allowedModules: string[]): void;

  /** Monitor resource usage */
  monitor(): ResourceUsage;
}

export interface PluginExecutionContext {
  /** Limited file system (only project directory + plugin directory) */
  fs: RestrictedFileSystem;

  /** No network access by default */
  net: null | RestrictedNetwork;

  /** Only whitelisted modules */
  require: (module: string) => unknown;

  /** Plugin-specific logger (no access to system logs) */
  logger: pino.Logger;
}

export interface ResourceUsage {
  cpuTime: number;
  memoryMb: number;
  fileHandles: number;
  networkRequests: number;
}
```

### 12.3 Data Isolation

```
Projects are completely isolated:
- Each project has its own directory tree
- Database rows are filtered by project_id (enforced at service layer)
- Memory entries scoped to project
- Evidence scoped to project
- Audit trail per project
- Git repositories per project
- No cross-project data access without explicit authorization
```

### 12.4 Audit Logging

```typescript
// Every mutation is logged to the audit table:
// - Who (actor: "user", "system", agent name)
// - What (action: project_created, phase_approved, etc.)
// - When (timestamp)
// - Where (project_id, entity_type, entity_id)
// - Details (JSON with before/after state for important changes)

// Example audit entries:
{
  "action": "phase_approved",
  "actor": "dr.smith@university.edu",
  "entityType": "phase",
  "entityId": "phase-literature-review-001",
  "details": {
    "projectId": "proj-neural-decision-making",
    "previousStatus": "awaiting_approval",
    "newStatus": "approved",
    "comments": "Literature review looks comprehensive"
  },
  "timestamp": "2026-07-30T14:30:00Z"
}
```

### 12.5 Input Validation

- All user input validated via Zod schemas before processing
- File paths validated to prevent path traversal
- Markdown content sanitized (no script injection if rendered in browser)
- Agent prompts validated for length and content
- Plugin manifests validated for required fields and permissions

---

## 13. Key Architectural Decisions

### Decision 1: Local-First with SQLite

**Choice:** SQLite as primary database via Drizzle ORM.

**Rationale:**
- Zero infrastructure requirements — runs on a laptop
- WAL mode provides concurrent reads with single-writer
- File-based — easy to backup, version, and inspect
- Handles research datasets up to ~100GB efficiently
- Migration path to PostgreSQL exists if needed (same Drizzle schema)

**Trade-offs:**
- Single-writer limitation (acceptable for single-user tool)
- No network access (acceptable for local-first requirement)
- Limited full-text search (acceptable — SQLite FTS5 available)

### Decision 2: Modular Monolith

**Choice:** Single process with clear module boundaries, not microservices.

**Rationale:**
- Developer tool, not a distributed system
- Single process simplifies crash recovery and state management
- Module boundaries enable future extraction to services if needed
- Dramatically simpler deployment and debugging

**Trade-offs:**
- Cannot scale horizontally (acceptable for single-user)
- All modules share process memory (acceptable for resource efficiency)
- Module coupling requires discipline (enforced by dependency rules)

### Decision 3: File System + Database Hybrid Storage

**Choice:** Markdown files for artifacts, SQLite for structured data.

**Rationale:**
- Markdown is human-readable, diffable, and Git-friendly
- SQLite provides fast queries, indexing, and aggregation
- File system provides natural backup via Git
- Separation of concerns: content vs. metadata

**Trade-offs:**
- Two storage systems to maintain (acceptable — clear boundary)
- Potential consistency issues (mitigated by transactional writes)
- File operations not atomic (mitigated by write-to-temp + rename)

### Decision 4: Phase-Based Execution with Checkpoints

**Choice:** Research projects execute as ordered phases with checkpoint/resume.

**Rationale:**
- Long-running projects (days/weeks) need crash recovery
- Checkpoints capture full state for reliable resume
- Human approval gates between phases ensure quality
- Phases provide natural units of work and review

**Trade-offs:**
- Sequential execution is slower than fully parallel (acceptable — quality over speed)
- Checkpoint overhead (acceptable — <1% of execution time)
- State serialization complexity (mitigated by JSON snapshots)

### Decision 5: Plugin System with Sandboxing

**Choice:** Dynamic plugin loading with restricted execution context.

**Rationale:**
- Extensibility without modifying core code
- Community contributions via plugins
- Sandboxing prevents plugins from breaking the system
- Permission model limits plugin capabilities

**Trade-offs:**
- Performance overhead of sandboxing (acceptable for plugin load times)
- Limited plugin capabilities (acceptable — security over flexibility)
- Plugin debugging complexity (mitigated by good error messages)

### Decision 6: Markdown-First Artifacts

**Choice:** All research artifacts stored as Markdown with YAML frontmatter.

**Rationale:**
- Human-readable and editable
- Version control friendly (meaningful diffs)
- Compatible with static site generators for publishing
- Extensible via YAML frontmatter
- Standard format that survives tool changes

**Trade-offs:**
- Not optimal for structured data (acceptable — use JSON sidecar files)
- Parsing overhead (acceptable — remark/unified ecosystem)
- Size limitations for large binary artifacts (acceptable — reference by path)

---

## Implementation Priority

**Phase 1 — Core Foundation (Week 1-2)**
1. `core/` — Types, errors, Result, events
2. `config/` — Configuration loading and validation
3. `db/` — SQLite schema, migrations, connection
4. `storage/` — File system operations, Git integration

**Phase 2 — Domain Services (Week 3-4)**
5. `memory/` — Memory management (short-term, long-term, episodic)
6. `evidence/` — Evidence collection and management
7. `approval/` — Human approval gates

**Phase 3 — Agent Orchestration (Week 5-6)**
8. `agents/` — Model providers, execution, pooling
9. `workflow/` — DAG execution engine, checkpoints

**Phase 4 — Integration (Week 7-8)**
10. `plugins/` — Plugin loading and sandboxing
11. `cli/` — Command-line interface
12. `http/` — Optional API layer

**Phase 5 — Production Readiness (Week 9-10)**
13. Observability — Logging, metrics, tracing
14. Security — Audit, secrets, input validation
15. Testing — Unit, integration, crash recovery tests
16. Documentation — Architecture docs, API reference, user guide
