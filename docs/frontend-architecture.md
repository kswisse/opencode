# Clippy — Frontend Architecture Specification

**Version:** 1.0.0  
**Stack:** Next.js 14 (App Router), TypeScript 5, Tailwind CSS 3, TanStack Query 5  
**Target:** Desktop-first (1280px+), no tablet/mobile for V1  
**Auth:** Hardcoded `tenantId` for V1 dev; NextAuth.js planned for production  
**Design Principle:** API-first — TypeScript interfaces define the contract; FastAPI backend implements to match.

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [API Type Definitions](#2-api-type-definitions)
3. [API Client](#3-api-client)
4. [WebSocket Hook & Pipeline](#4-websocket-hook--pipeline)
5. [Component Architecture](#5-component-architecture)
6. [State Management Strategy](#6-state-management-strategy)
7. [Server/Client Component Strategy](#7-serverclient-component-strategy)
8. [Keyboard Shortcuts System](#8-keyboard-shortcuts-system)
9. [Performance Optimization Plan](#9-performance-optimization-plan)
10. [Implementation Sequence](#10-implementation-sequence)

---

## 1. Project Structure

```
clippy/
├── apps/
│   └── frontend/
│       └── src/
│           ├── app/
│           │   ├── (dashboard)/
│           │   │   ├── layout.tsx            # Sidebar + topbar shell
│           │   │   ├── page.tsx              # Dashboard home (redirect → /videos)
│           │   │   ├── upload/
│           │   │   │   └── page.tsx          # File/URL upload (Client Component)
│           │   │   ├── videos/
│           │   │   │   ├── page.tsx          # Video list (Server Component)
│           │   │   │   └── [id]/
│           │   │   │       └── page.tsx      # Pipeline + candidates (Client Component)
│           │   │   ├── clips/
│           │   │   │   ├── page.tsx          # All generated clips (hybrid)
│           │   │   │   └── [id]/
│           │   │   │       └── page.tsx      # Clip detail + player (Client Component)
│           │   │   ├── analytics/
│           │   │   │   └── page.tsx          # Analytics overview (hybrid)
│           │   │   └── settings/
│           │   │       └── page.tsx          # Creator profile settings (Client Component)
│           │   ├── layout.tsx                # Root: providers, fonts, metadata
│           │   ├── page.tsx                  # Redirect / → /dashboard
│           │   └── favicon.ico
│           │
│           ├── components/
│           │   ├── ui/                       # Primitive design system
│           │   │   ├── button.tsx
│           │   │   ├── badge.tsx
│           │   │   ├── card.tsx
│           │   │   ├── input.tsx
│           │   │   ├── select.tsx
│           │   │   ├── toggle.tsx
│           │   │   ├── progress-bar.tsx
│           │   │   ├── skeleton.tsx
│           │   │   └── tooltip.tsx
│           │   │
│           │   ├── layout/
│           │   │   ├── sidebar.tsx
│           │   │   ├── topbar.tsx
│           │   │   └── page-container.tsx
│           │   │
│           │   ├── upload/
│           │   │   ├── upload-zone.tsx
│           │   │   ├── url-input.tsx
│           │   │   └── upload-progress.tsx
│           │   │
│           │   ├── pipeline/
│           │   │   ├── pipeline-stepper.tsx
│           │   │   └── step-indicator.tsx
│           │   │
│           │   ├── candidates/
│           │   │   ├── candidate-grid.tsx
│           │   │   ├── candidate-card.tsx
│           │   │   ├── score-badge.tsx
│           │   │   ├── bulk-actions.tsx
│           │   │   └── candidate-detail.tsx
│           │   │
│           │   ├── clips/
│           │   │   ├── clip-list.tsx
│           │   │   ├── clip-card.tsx
│           │   │   └── clip-player.tsx
│           │   │
│           │   ├── analytics/
│           │   │   ├── stats-card.tsx
│           │   │   ├── score-chart.tsx
│           │   │   └── overview-panel.tsx
│           │   │
│           │   └── settings/
│           │       ├── profile-form.tsx
│           │       ├── subtitle-style-picker.tsx
│           │       └── color-picker.tsx
│           │
│           ├── hooks/
│           │   ├── use-pipeline.ts
│           │   ├── use-candidates.ts
│           │   ├── use-analytics.ts
│           │   └── use-keyboard-shortcuts.ts
│           │
│           ├── lib/
│           │   ├── api.ts               # Fetch wrapper
│           │   ├── api-types.ts         # All TypeScript interfaces
│           │   ├── websocket.ts         # WebSocket connection manager
│           │   ├── upload.ts            # Upload utilities
│           │   └── utils.ts             # General utilities
│           │
│           ├── providers/
│           │   ├── query-provider.tsx
│           │   └── websocket-provider.tsx
│           │
│           └── styles/
│               └── globals.css
│
├── packages/
│   └── shared/                           # Shared types (separate npm workspace)
│       └── src/
│           └── types.ts                  # Mirrors api-types.ts for backend
│
├── apps/backend/                         # FastAPI (separate workspace)
├── turbo.json
├── package.json
└── tsconfig.json
```

---

## 2. API Type Definitions

**File:** `src/lib/api-types.ts`

```typescript
// ============================================================================
// Core Entities
// ============================================================================

/**
 * A video uploaded or linked by the user.
 * Broad source support: YouTube, Twitch, podcast RSS, local file upload.
 */
export interface Video {
  id: string;
  tenantId: string;
  title: string;
  sourceType: 'youtube' | 'twitch' | 'podcast' | 'local';
  /** Original URL for linked sources. Undefined for local uploads. */
  sourceUrl?: string;
  status: 'pending' | 'downloading' | 'processing' | 'ready' | 'failed';
  durationSeconds: number;
  fileSizeBytes: number;
  thumbnailUrl?: string;
  /** Flexible metadata: tags, notes, original filename, etc. */
  metadata: Record<string, unknown>;
  /** ISO 8601 */
  createdAt: string;
  /** Present when status === 'failed' */
  errorMessage?: string;
}

// ============================================================================
// Pipeline
// ============================================================================

export type PipelineStepName =
  | 'download'
  | 'transcribe'
  | 'analyze'
  | 'score'
  | 'generate'
  | 'done';

export interface PipelineStep {
  name: PipelineStepName;
  /** Human-readable label for the step */
  label: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  startedAt?: string;
  completedAt?: string;
  /** Present when status === 'failed' */
  errorMessage?: string;
}

// ============================================================================
// Scoring & Candidates
// ============================================================================

/**
 * Multi-dimensional scores for a clip candidate.
 * All values are 0-100 for consistent UX (progress bars, color scales).
 */
export interface ScoreSet {
  virality: number;      // 0-100
  retention: number;     // 0-100
  hook: number;          // 0-100
  emotion: number;       // 0-100
  shareability: number;  // 0-100
  educational: number;   // 0-100
}

/** A proposed clip segment from the AI analysis. */
export interface ClipCandidate {
  id: string;
  videoId: string;
  startTime: number;        // seconds from video start
  endTime: number;          // seconds from video start
  durationSeconds: number;
  thumbnailUrl: string;
  summary: string;
  scores: ScoreSet;
  /** Weighted aggregate of all scores (0-100). Sort key for ranking. */
  predictedScore: number;
  status: 'proposed' | 'approved' | 'rejected' | 'generated';
  createdAt: string;
}

// ============================================================================
// Clips (Generated)
// ============================================================================

/** A fully rendered, downloadable clip. */
export interface Clip {
  id: string;
  candidateId: string;
  videoId: string;
  /** Key in the storage bucket (S3/R2). */
  storageKey: string;
  title: string;
  durationSeconds: number;
  subtitleStyle: string;   // JSON-serialized style config
  format: 'mp4' | 'mov';
  resolution: string;      // e.g. "1080x1920"
  downloadUrl: string;
  thumbnailUrl: string;
  createdAt: string;
  analytics?: ClipAnalytics;
}

/** Performance metrics for a published clip. */
export interface ClipAnalytics {
  views: number;
  likes: number;
  shares: number;
  comments: number;
  watchTimeSeconds: number;
  /** 0-1 */
  completionRate: number;
  /** 0-1 */
  ctr: number;
  recordedAt: string;
}

// ============================================================================
// Analytics
// ============================================================================

export interface AnalyticsOverview {
  totalClips: number;
  totalViews: number;
  totalLikes: number;
  totalShares: number;
  averageCompletionRate: number;
  topClips: Clip[];
  /** How close predicted scores matched actual performance. 0-100. */
  scoreAccuracy: number;
}

// ============================================================================
// Creator Profile
// ============================================================================

export interface CreatorProfile {
  id: string;
  name: string;
  brandColors: {
    primary: string;    // hex
    secondary: string;  // hex
  };
  subtitleStyle: {
    font: string;
    color: string;
    position: 'bottom' | 'top';
    backgroundOpacity: number;  // 0-1
  };
  preferredDuration: number;  // seconds, target clip length
  autoEditPreferences: {
    zoomStyle: 'static' | 'dynamic' | 'speaker-follow';
    backgroundBlur: boolean;
    silenceRemoval: boolean;
  };
  createdAt: string;
}

// ============================================================================
// API Response Wrappers
// ============================================================================

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiErrorBody {
  detail: string;
  code?: string;
  field?: string;
}

// ============================================================================
// API Endpoint Response Shapes
// ============================================================================

export namespace Responses {
  export type GetUploadUrl = { url: string; fields: Record<string, string> };
  export type ConfirmVideo = Video;
  export type GetVideos = PaginatedResponse<Video>;
  export type GetVideo = { video: Video; pipeline: PipelineStep[] };
  export type GetCandidates = { candidates: ClipCandidate[] };
  export type ApproveCandidate = { clip: Clip };
  export type RejectCandidate = { ok: boolean };
  export type BatchApprove = { clips: Clip[] };
  export type BatchReject = { ok: boolean };
  export type GetClips = { clips: Clip[] };
  export type GetClip = { clip: Clip };
  export type GetAnalyticsOverview = AnalyticsOverview;
  export type GetProfile = CreatorProfile;
  export type UpdateProfile = CreatorProfile;
}
```

---

## 3. API Client

**File:** `src/lib/api.ts`

```typescript
import type { Responses } from './api-types';

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TENANT_ID = process.env.NEXT_PUBLIC_TENANT_ID || 'dev-tenant-1';

// ============================================================================
// Error Handling
// ============================================================================

export class ApiError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly field?: string;

  constructor(status: number, body: { detail?: string; code?: string; field?: string }) {
    super(body.detail || `API request failed with status ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.code = body.code;
    this.field = body.field;
  }
}

// ============================================================================
// Core Fetch Wrapper
// ============================================================================

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  params?: Record<string, string | number | undefined>;
  headers?: Record<string, string>;
};

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, params, headers = {} } = options;

  // Build URL with query params
  let url = `${API_BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) searchParams.set(key, String(value));
    });
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  // Build headers
  const finalHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Tenant-Id': TENANT_ID,
    ...headers,
  };

  const response = await fetch(url, {
    method,
    headers: finalHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });

  // Handle errors
  if (!response.ok) {
    let errorBody: { detail?: string; code?: string; field?: string } = {};
    try {
      errorBody = await response.json();
    } catch {
      errorBody = { detail: response.statusText };
    }
    throw new ApiError(response.status, errorBody);
  }

  // Handle 204 No Content
  if (response.status === 204) return undefined as T;

  return response.json() as Promise<T>;
}

// ============================================================================
// Convenience Methods
// ============================================================================

const get = <T>(endpoint: string, params?: Record<string, string | number | undefined>) =>
  request<T>(endpoint, { params });

const post = <T>(endpoint: string, body?: unknown) =>
  request<T>(endpoint, { method: 'POST', body });

const patch = <T>(endpoint: string, body?: unknown) =>
  request<T>(endpoint, { method: 'PATCH', body });

const del = <T>(endpoint: string) =>
  request<T>(endpoint, { method: 'DELETE' });

// ============================================================================
// Public API
// ============================================================================

export const api = {
  // ─── Videos ──────────────────────────────────────────────────────────
  getUploadUrl: () => post<Responses['GetUploadUrl']>('/videos/upload-url'),

  confirmVideo: (data: {
    storageKey: string;
    sourceType: string;
    metadata?: Record<string, unknown>;
  }) => post<Responses['ConfirmVideo']>('/videos/confirm', data),

  getVideos: (params?: { status?: string; limit?: number; offset?: number }) =>
    get<Responses['GetVideos']>('/videos', params as Record<string, string | number | undefined>),

  getVideo: (id: string) =>
    get<Responses['GetVideo']>(`/videos/${id}`),

  // ─── Candidates ──────────────────────────────────────────────────────
  getCandidates: (videoId: string) =>
    get<Responses['GetCandidates']>(`/videos/${videoId}/candidates`),

  approveCandidate: (id: string) =>
    post<Responses['ApproveCandidate']>(`/candidates/${id}/approve`),

  rejectCandidate: (id: string, reason?: string) =>
    post<Responses['RejectCandidate']>(`/candidates/${id}/reject`, { reason }),

  batchApprove: (ids: string[]) =>
    post<Responses['BatchApprove']>('/candidates/batch/approve', { ids }),

  batchReject: (ids: string[]) =>
    post<Responses['BatchReject']>('/candidates/batch/reject', { ids }),

  // ─── Clips ───────────────────────────────────────────────────────────
  getClips: () => get<Responses['GetClips']>('/clips'),

  getClip: (id: string) => get<Responses['GetClip']>(`/clips/${id}`),

  // ─── Analytics ───────────────────────────────────────────────────────
  getAnalyticsOverview: () => get<Responses['GetAnalyticsOverview']>('/analytics/overview'),

  // ─── Profile ─────────────────────────────────────────────────────────
  getProfile: () => get<Responses['GetProfile']>('/profile'),

  updateProfile: (data: Partial<CreatorProfile>) =>
    patch<Responses['UpdateProfile']>('/profile', data),
};
```

---

## 4. WebSocket Hook & Pipeline

### 4.1 WebSocket Connection Manager

**File:** `src/lib/websocket.ts`

```typescript
type MessageHandler = (data: unknown) => void;
type StatusListener = (status: ConnectionStatus) => void;

export type ConnectionStatus = 'connected' | 'disconnected' | 'reconnecting';

interface WebSocketConfig {
  url: string;
  onMessage: MessageHandler;
  onStatusChange?: StatusListener;
  /** Base delay in ms for exponential backoff */
  baseDelay?: number;
  /** Maximum delay in ms */
  maxDelay?: number;
}

/**
 * Manages a single WebSocket connection with automatic reconnection
 * using exponential backoff (1s, 2s, 4s, 8s, 16s, max 30s).
 */
export class WebSocketConnection {
  private ws: WebSocket | null = null;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private closed = false;
  private config: WebSocketConfig;

  constructor(config: WebSocketConfig) {
    this.config = {
      baseDelay: 1000,
      maxDelay: 30000,
      ...config,
    };
    this.connect();
  }

  connect(): void {
    if (this.closed) return;

    this.config.onStatusChange?.('reconnecting');
    this.ws = new WebSocket(this.config.url);

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.config.onStatusChange?.('connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.config.onMessage(data);
      } catch (err) {
        console.error('[WS] Failed to parse message:', err);
      }
    };

    this.ws.onclose = () => {
      if (this.closed) {
        this.config.onStatusChange?.('disconnected');
        return;
      }
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      // onclose fires after onerror, so reconnection is handled there
      this.ws?.close();
    };
  }

  private scheduleReconnect(): void {
    const delay = Math.min(
      this.config.baseDelay! * Math.pow(2, this.reconnectAttempt),
      this.config.maxDelay!
    );
    this.reconnectAttempt++;
    this.config.onStatusChange?.('reconnecting');

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /** Send a JSON message. Safe to call even when disconnected. */
  send(data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('[WS] Cannot send — socket not open');
    }
  }

  /** Gracefully close the connection. No reconnect will be attempted. */
  disconnect(): void {
    this.closed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this.config.onStatusChange?.('disconnected');
  }
}
```

### 4.2 Pipeline Update Hook

**File:** `src/hooks/use-pipeline.ts`

```typescript
'use client';

import { useEffect, useCallback, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WebSocketConnection, ConnectionStatus } from '@/lib/websocket';
import type { PipelineStep } from '@/lib/api-types';

interface PipelineEvent {
  type: 'pipeline.step_update' | 'pipeline.completed' | 'pipeline.failed';
  videoId: string;
  step?: PipelineStep;
  error?: string;
}

interface UsePipelineReturn {
  /** Current pipeline steps. Undefined while loading or when no pipeline exists. */
  steps: PipelineStep[] | undefined;
  /** WebSocket connection status */
  connectionStatus: ConnectionStatus;
  /** Error message from a pipeline failure event */
  error?: string;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

/**
 * Manages a WebSocket connection for real-time pipeline updates.
 *
 * - Connects on mount when videoId is provided
 * - Disconnects on unmount or when videoId changes
 * - Updates React Query cache on pipeline events
 * - Reconnects automatically with exponential backoff
 *
 * @param videoId - The video to subscribe to. Undefined = no connection.
 */
export function usePipeline(videoId: string | undefined): UsePipelineReturn {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocketConnection | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [error, setError] = useState<string | undefined>();
  const [steps, setSteps] = useState<PipelineStep[] | undefined>();

  const handleMessage = useCallback(
    (data: PipelineEvent) => {
      switch (data.type) {
        case 'pipeline.step_update':
          // Update live steps state
          setSteps((prev) => {
            if (!prev) return data.step ? [data.step] : prev;
            return prev.map((s) =>
              s.name === data.step?.name ? { ...s, ...data.step } : s
            );
          });
          // Also invalidate React Query cache so server data stays fresh
          queryClient.invalidateQueries({
            queryKey: ['videos', 'detail', data.videoId],
          });
          break;

        case 'pipeline.completed':
          setSteps((prev) =>
            prev?.map((s) =>
              s.name === 'done' ? { ...s, status: 'completed' as const } : s
            )
          );
          queryClient.invalidateQueries({
            queryKey: ['videos', 'detail', data.videoId],
          });
          break;

        case 'pipeline.failed':
          setError(data.error);
          queryClient.invalidateQueries({
            queryKey: ['videos', 'detail', data.videoId],
          });
          break;
      }
    },
    [queryClient]
  );

  const handleStatusChange = useCallback((status: ConnectionStatus) => {
    setConnectionStatus(status);
  }, []);

  useEffect(() => {
    if (!videoId) {
      setConnectionStatus('disconnected');
      return;
    }

    const ws = new WebSocketConnection({
      url: `${WS_BASE_URL}/ws/videos/${videoId}`,
      onMessage: handleMessage,
      onStatusChange: handleStatusChange,
    });
    wsRef.current = ws;

    // Fetch initial pipeline state from REST
    queryClient
      .fetchQuery({
        queryKey: ['videos', 'detail', videoId],
      })
      .then((data: any) => {
        if (data?.pipeline) setSteps(data.pipeline);
      })
      .catch(console.error);

    return () => {
      ws.disconnect();
      wsRef.current = null;
      setSteps(undefined);
      setError(undefined);
    };
  }, [videoId, handleMessage, handleStatusChange, queryClient]);

  return { steps, connectionStatus, error };
}
```

---

## 5. Component Architecture

### 5.1 Primitive UI Components

**File:** `src/components/ui/button.tsx`

```typescript
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500',
        secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-400',
        danger: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500',
        ghost: 'hover:bg-gray-100 text-gray-700 focus-visible:ring-gray-400',
      },
      size: {
        sm: 'h-8 px-3 text-sm gap-1.5',
        md: 'h-10 px-4 text-sm gap-2',
        lg: 'h-12 px-6 text-base gap-2',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, leftIcon, rightIcon, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={buttonVariants({ variant, size, className })}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : leftIcon ? (
          leftIcon
        ) : null}
        {children}
        {!loading && rightIcon}
      </button>
    );
  }
);
Button.displayName = 'Button';
```

### 5.2 CandidateCard Component

**File:** `src/components/candidates/candidate-card.tsx`

```typescript
'use client';

import { useRef, useState, useCallback, type KeyboardEvent } from 'react';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { ClipCandidate } from '@/lib/api-types';

interface CandidateCardProps {
  candidate: ClipCandidate;
  isSelected: boolean;
  onSelect: (id: string) => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  onPreview: (id: string) => void;
}

/**
 * A card representing a single clip candidate.
 *
 * Supporting states:
 * - **Default**: Thumbnail, score badges, approve/reject buttons
 * - **Selected**: Blue border + selected check indicator
 * - **Hover**: Card lifts slightly, play overlay appears on thumbnail
 * - **Approving**: Optimistic — card hides with brief green flash (CSS animation)
 * - **Rejecting**: Optimistic — card fades out with brief red transition
 * - **Keyboard**: 'a' approve, 'r' reject when card is focused
 */
export function CandidateCard({
  candidate,
  isSelected,
  onSelect,
  onApprove,
  onReject,
  onPreview,
}: CandidateCardProps) {
  const [animState, setAnimState] = useState<'idle' | 'approving' | 'rejecting'>('idle');
  const cardRef = useRef<HTMLDivElement>(null);

  const handleApprove = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setAnimState('approving');
      // Brief animation before actual API call
      setTimeout(() => onApprove(candidate.id), 300);
    },
    [candidate.id, onApprove]
  );

  const handleReject = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setAnimState('rejecting');
      setTimeout(() => onReject(candidate.id), 300);
    },
    [candidate.id, onReject]
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'a' || e.key === 'A') {
        e.preventDefault();
        handleApprove(e as unknown as React.MouseEvent);
      }
      if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        handleReject(e as unknown as React.MouseEvent);
      }
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onPreview(candidate.id);
      }
    },
    [candidate.id, onApprove, onPreview, onReject]
  );

  const scoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div
      ref={cardRef}
      role="article"
      tabIndex={0}
      aria-label={`Candidate clip: ${candidate.summary.slice(0, 60)}...`}
      className={cn(
        'group relative rounded-xl border-2 bg-white p-3 transition-all duration-200 cursor-pointer',
        'hover:shadow-lg hover:-translate-y-0.5',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
        // Selected state
        isSelected && 'border-blue-500 shadow-md',
        !isSelected && 'border-gray-200',
        // Animation states
        animState === 'approving' && 'animate-green-flash opacity-0 scale-95',
        animState === 'rejecting' && 'animate-red-fade opacity-0',
        animState === 'idle' && 'opacity-100 scale-100'
      )}
      onClick={() => onSelect(candidate.id)}
      onKeyDown={handleKeyDown}
    >
      {/* Thumbnail with play overlay on hover */}
      <div
        className="relative aspect-video mb-3 rounded-lg overflow-hidden bg-gray-100"
        onClick={(e) => {
          e.stopPropagation();
          onPreview(candidate.id);
        }}
      >
        <Image
          src={candidate.thumbnailUrl}
          alt={`Thumbnail for ${candidate.summary.slice(0, 40)}`}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 33vw"
        />
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
          <span className="opacity-0 group-hover:opacity-100 text-white text-4xl transition-opacity">
            ▶
          </span>
        </div>
        {/* Duration badge */}
        <span className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-0.5 rounded">
          {candidate.durationSeconds}s
        </span>
      </div>

      {/* Summary */}
      <p className="text-sm text-gray-700 line-clamp-2 mb-3">
        {candidate.summary}
      </p>

      {/* Score badges */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        <ScoreBadge label="Overall" score={candidate.predictedScore} />
        <ScoreBadge label="Viral" score={candidate.scores.virality} />
        <ScoreBadge label="Hook" score={candidate.scores.hook} />
      </div>

      {/* Actions */}
      <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
        <Button
          variant="primary"
          size="sm"
          onClick={handleApprove}
          className="flex-1"
          aria-label={`Approve candidate ${candidate.id}`}
        >
          ✓ Approve
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReject}
          className="flex-1 text-gray-500"
          aria-label={`Reject candidate ${candidate.id}`}
        >
          ✕ Reject
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// Internal ScoreBadge
// ============================================================================

function ScoreBadge({ label, score }: { label: string; score: number }) {
  const color =
    score >= 80
      ? 'bg-green-100 text-green-800'
      : score >= 60
      ? 'bg-yellow-100 text-yellow-800'
      : 'bg-red-100 text-red-800';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${color}`}
      title={`${label}: ${score}/100`}
    >
      {label}: {score}
    </span>
  );
}

// ============================================================================
// CSS Animations (add to globals.css or use tailwind config)
// ============================================================================
// @keyframes green-flash {
//   0% { background-color: transparent; }
//   50% { background-color: rgba(34, 197, 94, 0.2); }
//   100% { background-color: transparent; }
// }
// @keyframes red-fade {
//   0% { opacity: 1; background-color: transparent; }
//   50% { background-color: rgba(239, 68, 68, 0.15); }
//   100% { opacity: 0; }
// }
```

### 5.3 PipelineStepper Component

**File:** `src/components/pipeline/pipeline-stepper.tsx`

```typescript
'use client';

import { cn } from '@/lib/utils';
import type { PipelineStep, PipelineStepName } from '@/lib/api-types';

interface PipelineStepperProps {
  steps: PipelineStep[];
  className?: string;
}

const STEP_ORDER: PipelineStepName[] = [
  'download',
  'transcribe',
  'analyze',
  'score',
  'generate',
  'done',
];

const STEP_LABELS: Record<PipelineStepName, string> = {
  download: 'Download',
  transcribe: 'Transcribe',
  analyze: 'Analyze',
  score: 'Score',
  generate: 'Generate',
  done: 'Done',
};

/**
 * Visual pipeline progress stepper.
 *
 * Fixed order with 6 steps. Each step renders as a circle + label.
 * Connecting lines flow between circles with appropriate coloring.
 *
 * Visual states per step:
 * - **pending**:  gray circle, gray label
 * - **active**:   blue circle with pulse animation, blue label
 * - **completed**: green circle with checkmark, green label
 * - **failed**:   red circle with X, red label + error tooltip on hover
 */
export function PipelineStepper({ steps, className }: PipelineStepperProps) {
  if (!steps.length) return null;

  return (
    <nav aria-label="Pipeline progress" className={cn('w-full', className)}>
      <ol className="flex items-center justify-between">
        {STEP_ORDER.map((stepName, index) => {
          const step = steps.find((s) => s.name === stepName);
          const status = step?.status || 'pending';

          return (
            <li key={stepName} className="relative flex flex-col items-center flex-1">
              {/* Connecting line before this step (except first step) */}
              {index > 0 && (
                <div
                  className={cn(
                    'absolute top-4 right-1/2 w-full h-0.5 -z-10',
                    getLineColor(STEP_ORDER[index - 1], steps)
                  )}
                  style={{ transform: 'translateY(-50%)' }}
                />
              )}

              {/* Step circle */}
              <div
                className={cn(
                  'relative flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all',
                  getCircleStyle(status),
                  status === 'active' && 'animate-pulse'
                )}
                title={step?.errorMessage}
              >
                {status === 'completed' && (
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {status === 'failed' && (
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
                {status === 'active' && (
                  <span className="w-3 h-3 bg-blue-500 rounded-full" />
                )}
              </div>

              {/* Label */}
              <span
                className={cn(
                  'mt-2 text-xs font-medium',
                  status === 'pending' && 'text-gray-400',
                  status === 'active' && 'text-blue-600',
                  status === 'completed' && 'text-green-600',
                  status === 'failed' && 'text-red-600'
                )}
              >
                {STEP_LABELS[stepName]}
              </span>

              {/* Error tooltip */}
              {status === 'failed' && step?.errorMessage && (
                <div className="absolute top-10 mt-6 w-48 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700 text-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                  {step.errorMessage}
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function getCircleStyle(status: PipelineStep['status']): string {
  switch (status) {
    case 'completed':
      return 'bg-green-500 border-green-500 text-white';
    case 'active':
      return 'border-blue-500 bg-blue-50 text-blue-600';
    case 'failed':
      return 'border-red-500 bg-red-500 text-white';
    case 'pending':
    default:
      return 'border-gray-300 bg-white text-gray-400';
  }
}

function getLineColor(previousStepName: PipelineStepName, steps: PipelineStep[]): string {
  const prevStep = steps.find((s) => s.name === previousStepName);
  if (!prevStep) return 'bg-gray-200';
  switch (prevStep.status) {
    case 'completed':
      return 'bg-green-500';
    case 'active':
      return 'bg-blue-500';
    case 'failed':
      return 'bg-red-500';
    default:
      return 'bg-gray-200';
  }
}
```

### 5.4 UploadZone Component

**File:** `src/components/upload/upload-zone.tsx`

```typescript
'use client';

import { useState, useRef, useCallback, type DragEvent } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ProgressBar } from '@/components/ui/progress-bar';

interface UploadZoneProps {
  onFileSelected: (file: File) => void;
  onUrlSubmit: (url: string) => void;
  className?: string;
}

/**
 * Upload zone supporting both file drag-and-drop and URL input.
 *
 * States:
 * - **Default**: Dashed border drop zone + URL input below
 * - **Drag over**: Blue border, subtle blue background highlight
 * - **Uploading**: Progress bar, percentage, file name shown
 * - **YouTube URL detected**: Shows YouTube badge on the URL
 * - **Error**: Border turns red, error message below
 * - **Success**: Brief check animation, redirect to pipeline page
 */
export function UploadZone({ onFileSelected, onUrlSubmit, className }: UploadZoneProps) {
  const [dragState, setDragState] = useState<'idle' | 'dragover' | 'uploading' | 'error' | 'success'>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [urlValue, setUrlValue] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isYouTubeUrl = (url: string): boolean => {
    return /(youtube\.com|youtu\.be)/i.test(url);
  };

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragState('dragover');
  }, []);

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragState('idle');
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();

      const file = e.dataTransfer.files[0];
      if (!file) {
        setDragState('error');
        setErrorMessage('No file detected in drop.');
        return;
      }

      // Validate file type
      const validTypes = ['video/mp4', 'video/quicktime', 'video/webm', 'video/x-matroska'];
      if (!validTypes.includes(file.type)) {
        setDragState('error');
        setErrorMessage(`Unsupported file type: ${file.type}. Upload MP4, MOV, WebM, or MKV.`);
        return;
      }

      setDragState('uploading');
      setErrorMessage('');
      simulateUpload(file);
    },
    [onFileSelected]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      setDragState('uploading');
      simulateUpload(file);
    },
    [onFileSelected]
  );

  const handleUrlSubmit = useCallback(() => {
    if (!urlValue.trim()) {
      setDragState('error');
      setErrorMessage('Please enter a URL.');
      return;
    }

    try {
      new URL(urlValue); // validate URL format
    } catch {
      setDragState('error');
      setErrorMessage('Invalid URL format. Please enter a valid URL.');
      return;
    }

    setDragState('uploading');
    setErrorMessage('');
    // For URL-based uploads, we skip file selection
    onUrlSubmit(urlValue);
    // Simulate briefly
    setUploadProgress(100);
    setDragState('success');
  }, [urlValue, onUrlSubmit]);

  /** Simulated upload progress for demo. Replace with real XHR upload. */
  const simulateUpload = (file: File) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setUploadProgress(100);
        setDragState('success');
        onFileSelected(file);
      }
      setUploadProgress(Math.min(progress, 100));
    }, 300);
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Drop Zone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload video file via drag and drop or click to browse"
        className={cn(
          'relative flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-12 transition-all duration-200',
          dragState === 'idle' && 'border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100',
          dragState === 'dragover' && 'border-blue-500 bg-blue-50',
          dragState === 'uploading' && 'border-blue-400 bg-blue-50',
          dragState === 'error' && 'border-red-400 bg-red-50',
          dragState === 'success' && 'border-green-500 bg-green-50',
          'cursor-pointer'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click();
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/mp4,video/quicktime,video/webm,video/x-matroska"
          className="hidden"
          onChange={handleFileSelect}
          aria-hidden="true"
        />

        {dragState === 'idle' && (
          <>
            <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-lg font-medium text-gray-700">
              Drop video file here
            </p>
            <p className="text-sm text-gray-500 mt-1">
              or click to browse — MP4, MOV, WebM, MKV
            </p>
          </>
        )}

        {dragState === 'dragover' && (
          <>
            <svg className="w-12 h-12 text-blue-500 mb-4 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
            <p className="text-lg font-medium text-blue-600">
              Drop to upload
            </p>
          </>
        )}

        {dragState === 'uploading' && (
          <div className="w-full max-w-sm space-y-3">
            <p className="text-sm font-medium text-blue-700 text-center">Uploading...</p>
            <ProgressBar value={uploadProgress} max={100} className="w-full" />
            <p className="text-xs text-gray-500 text-center">{Math.round(uploadProgress)}%</p>
          </div>
        )}

        {dragState === 'success' && (
          <>
            <svg className="w-12 h-12 text-green-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-lg font-medium text-green-700">
              Upload complete!
            </p>
            <p className="text-sm text-green-600">Redirecting to pipeline...</p>
          </>
        )}

        {dragState === 'error' && (
          <>
            <svg className="w-12 h-12 text-red-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <p className="text-lg font-medium text-red-700">Upload failed</p>
            <p className="text-sm text-red-600">{errorMessage}</p>
            <Button
              variant="ghost"
              size="sm"
              className="mt-2"
              onClick={(e) => {
                e.stopPropagation();
                setDragState('idle');
                setErrorMessage('');
              }}
            >
              Try again
            </Button>
          </>
        )}
      </div>

      {/* Divider */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-px bg-gray-200" />
        <span className="text-sm text-gray-400">or paste a link</span>
        <div className="flex-1 h-px bg-gray-200" />
      </div>

      {/* URL Input */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Input
            type="url"
            placeholder="https://youtube.com/watch?v=... or https://twitch.tv/..."
            value={urlValue}
            onChange={(e) => setUrlValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleUrlSubmit()}
            className={cn(
              dragState === 'error' && 'border-red-400 focus-visible:ring-red-400'
            )}
            aria-label="Video URL input"
          />
          {isYouTubeUrl(urlValue) && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
              YouTube
            </span>
          )}
        </div>
        <Button onClick={handleUrlSubmit} disabled={!urlValue.trim()}>
          Add Link
        </Button>
      </div>

      {dragState === 'error' && errorMessage && (
        <p className="text-sm text-red-600" role="alert">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
```

### 5.5 Layout Components

**File:** `src/components/layout/sidebar.tsx`

```typescript
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: 'Upload',
    href: '/upload',
    icon: <UploadIcon />,
  },
  {
    label: 'Videos',
    href: '/videos',
    icon: <VideoIcon />,
  },
  {
    label: 'Clips',
    href: '/clips',
    icon: <ClipIcon />,
  },
  {
    label: 'Analytics',
    href: '/analytics',
    icon: <AnalyticsIcon />,
  },
  {
    label: 'Settings',
    href: '/settings',
    icon: <SettingsIcon />,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-full w-64 border-r border-gray-200 bg-white">
      {/* Logo */}
      <div className="flex items-center gap-2 px-6 py-5 border-b border-gray-100">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <span className="text-white font-bold text-sm">C</span>
        </div>
        <span className="text-lg font-semibold text-gray-900">Clippy</span>
      </div>

      {/* Navigation */}
      <nav className="px-3 py-4" aria-label="Main navigation">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  )}
                >
                  {item.icon}
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100">
        <p className="text-xs text-gray-400 text-center">Clippy v1.0.0</p>
      </div>
    </aside>
  );
}

// Simple inline SVG icons
function UploadIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  );
}
function VideoIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9A2.25 2.25 0 004.5 18.75z" />
    </svg>
  );
}
function ClipIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
    </svg>
  );
}
function AnalyticsIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  );
}
function SettingsIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}
```

---

## 6. State Management Strategy

### 6.1 Query Key Factory

**File:** `src/lib/query-keys.ts`

```typescript
export const queryKeys = {
  videos: {
    all: ['videos'] as const,
    list: (params?: Record<string, unknown>) =>
      ['videos', 'list', params] as const,
    detail: (id: string) => ['videos', 'detail', id] as const,
  },
  candidates: {
    all: ['candidates'] as const,
    byVideo: (videoId: string) => ['candidates', videoId] as const,
  },
  clips: {
    all: ['clips'] as const,
    detail: (id: string) => ['clips', 'detail', id] as const,
  },
  analytics: {
    overview: ['analytics', 'overview'] as const,
  },
  profile: {
    me: ['profile', 'me'] as const,
  },
};
```

### 6.2 Custom Query Hooks

**File:** `src/hooks/use-candidates.ts`

```typescript
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { queryKeys } from '@/lib/query-keys';
import type { ClipCandidate } from '@/lib/api-types';

/**
 * Fetches all candidates for a given video.
 */
export function useCandidates(videoId: string) {
  return useQuery({
    queryKey: queryKeys.candidates.byVideo(videoId),
    queryFn: () => api.getCandidates(videoId),
    staleTime: 30_000, // 30s — candidates change infrequently
    select: (data) => data.candidates,
  });
}

/**
 * Approve a candidate with optimistic removal from the list.
 */
export function useApproveCandidate(videoId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.approveCandidate(id),
    onMutate: async (id) => {
      const queryKey = queryKeys.candidates.byVideo(videoId);
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<{ candidates: ClipCandidate[] }>(queryKey);

      queryClient.setQueryData(queryKey, (old?: { candidates: ClipCandidate[] }) => {
        if (!old) return old;
        return { candidates: old.candidates.filter((c) => c.id !== id) };
      });

      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.candidates.byVideo(videoId), context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.candidates.byVideo(videoId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.clips.all });
    },
  });
}

/**
 * Reject a candidate with optimistic removal from the list.
 */
export function useRejectCandidate(videoId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.rejectCandidate(id),
    onMutate: async (id) => {
      const queryKey = queryKeys.candidates.byVideo(videoId);
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<{ candidates: ClipCandidate[] }>(queryKey);

      queryClient.setQueryData(queryKey, (old?: { candidates: ClipCandidate[] }) => {
        if (!old) return old;
        return { candidates: old.candidates.filter((c) => c.id !== id) };
      });

      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.candidates.byVideo(videoId), context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.candidates.byVideo(videoId) });
    },
  });
}

/**
 * Batch approve multiple candidates at once.
 */
export function useBatchApprove(videoId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: string[]) => api.batchApprove(ids),
    onMutate: async (ids) => {
      const queryKey = queryKeys.candidates.byVideo(videoId);
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<{ candidates: ClipCandidate[] }>(queryKey);

      queryClient.setQueryData(queryKey, (old?: { candidates: ClipCandidate[] }) => {
        if (!old) return old;
        return { candidates: old.candidates.filter((c) => !ids.includes(c.id)) };
      });

      return { previous };
    },
    onError: (_err, _ids, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.candidates.byVideo(videoId), context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.candidates.byVideo(videoId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.clips.all });
    },
  });
}
```

### 6.3 Analytics Hook

**File:** `src/hooks/use-analytics.ts`

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { queryKeys } from '@/lib/query-keys';

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: queryKeys.analytics.overview,
    queryFn: () => api.getAnalyticsOverview(),
    staleTime: 60_000, // 1 minute — analytics don't change by the second
    refetchInterval: 120_000, // Auto-refresh every 2 minutes
  });
}
```

### 6.4 Query Provider Setup

**File:** `src/providers/query-provider.tsx`

```typescript
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState, type ReactNode } from 'react';

interface QueryProviderProps {
  children: ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            gcTime: 5 * 60_000, // 5 minutes
            retry: 2,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: 0,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

---

## 7. Server / Client Component Strategy

| Page | Route | Component Type | Rationale |
|---|---|---|---|
| Dashboard (redirect) | `/` | Server | Simple redirect to `/videos` |
| Upload | `/upload` | **Client** | File handling, drag-drop, Web API, URL validation |
| Video list | `/videos` | **Server** | Fetch list on server, render links to detail pages |
| Video detail | `/videos/[id]` | **Client** | Real-time WebSocket pipeline, interactive candidate review grid |
| Clip list | `/clips` | Server + Client island | Server-fetched list, interactive filter bar as client island |
| Clip detail | `/clips/[id]` | **Client** | Video player, download interactions, share buttons |
| Analytics | `/analytics` | Server + Client islands | Data fetched on server, chart widgets as client islands |
| Settings | `/settings` | **Client** | Complex form state, live preview of subtitle styles |

### Pattern for Hybrid Pages (e.g., Analytics)

```typescript
// src/app/(dashboard)/analytics/page.tsx — Server Component
import { api } from '@/lib/api-server'; // Server-only fetch wrapper
import { AnalyticsClient } from './analytics-client';
import type { AnalyticsOverview } from '@/lib/api-types';

export default async function AnalyticsPage() {
  // Data fetched on the server — no loading state needed
  let data: AnalyticsOverview;
  try {
    data = await api.getAnalyticsOverview();
  } catch {
    return <ErrorState message="Failed to load analytics" />;
  }

  return <AnalyticsClient initialData={data} />;
}

// analytics-client.tsx — Client Component
'use client';

import { useAnalyticsOverview } from '@/hooks/use-analytics';
import { StatsCard } from '@/components/analytics/stats-card';
import { ScoreChart } from '@/components/analytics/score-chart';
import type { AnalyticsOverview } from '@/lib/api-types';

export function AnalyticsClient({ initialData }: { initialData: AnalyticsOverview }) {
  // Hydrate from server data, then keep fresh via refetchInterval
  const { data } = useAnalyticsOverview(initialData);

  if (!data) return <LoadingSkeleton />;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <StatsCard label="Total Clips" value={data.totalClips} />
        <StatsCard label="Total Views" value={data.totalViews} />
        <StatsCard label="Total Likes" value={data.totalLikes} />
        <StatsCard label="Avg Completion" value={`${(data.averageCompletionRate * 100).toFixed(0)}%`} />
      </div>
      <ScoreChart scoreAccuracy={data.scoreAccuracy} />
    </div>
  );
}
```

---

## 8. Keyboard Shortcuts System

**File:** `src/hooks/use-keyboard-shortcuts.ts`

```typescript
'use client';

import { useEffect, useCallback, useRef } from 'react';

export interface ShortcutMap {
  /** Approve the currently selected/focused candidate */
  'a'?: () => void;
  /** Reject the currently selected/focused candidate */
  'r'?: () => void;
  /** Navigate to the previous candidate */
  'ArrowLeft'?: () => void;
  /** Navigate to the next candidate */
  'ArrowRight'?: () => void;
  /** Play/pause the preview video */
  ' '?: () => void;
  /** Close a detail modal or deselect */
  'Escape'?: () => void;
}

type KeyMap = Record<string, () => void>;

/**
 * Registers global keyboard shortcuts scoped to an enabled state.
 *
 * - **Only fires when no input/textarea/select is focused** (prevents
 *   accidental activations while typing in forms).
 * - Respects the `enabled` flag — useful for conditional activation
 *   within specific views.
 * - Cleans up on unmount.
 *
 * @example
 * ```tsx
 * useKeyboardShortcuts({
 *   'a': handleApprove,
 *   'r': handleReject,
 *   ' ': togglePreview,
 *   'Escape': closeDetail,
 * });
 * ```
 */
export function useKeyboardShortcuts(
  shortcuts: ShortcutMap,
  enabled: boolean = true
): void {
  const shortcutsRef = useRef<ShortcutMap>(shortcuts);
  shortcutsRef.current = shortcuts;

  const handler = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Don't trigger shortcuts when user is typing in a form field
      const target = event.target as HTMLElement;
      const isInputFocused =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable;

      if (isInputFocused) return;

      const key = event.key;
      const action = shortcutsRef.current[key as keyof ShortcutMap];

      if (action) {
        event.preventDefault();
        action();
      }
    },
    [enabled]
  );

  useEffect(() => {
    if (!enabled) return;

    document.addEventListener('keydown', handler);

    return () => {
      document.removeEventListener('keydown', handler);
    };
  }, [enabled, handler]);
}
```

### Usage in Candidate Review Page

```typescript
// Inside src/app/(dashboard)/videos/[id]/page.tsx
'use client';

import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { useCandidates, useApproveCandidate, useRejectCandidate } from '@/hooks/use-candidates';
import { usePipeline } from '@/hooks/use-pipeline';
import { CandidateGrid } from '@/components/candidates/candidate-grid';
import { PipelineStepper } from '@/components/pipeline/pipeline-stepper';
import { useState } from 'react';

export default function VideoDetailPage({ params }: { params: { id: string } }) {
  const videoId = params.id;
  const { data: candidates, isLoading } = useCandidates(videoId);
  const { steps, connectionStatus } = usePipeline(videoId);
  const approveMutation = useApproveCandidate(videoId);
  const rejectMutation = useRejectCandidate(videoId);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [previewId, setPreviewId] = useState<string | null>(null);

  useKeyboardShortcuts({
    'a': () => {
      if (selectedId) approveMutation.mutate(selectedId);
    },
    'r': () => {
      if (selectedId) rejectMutation.mutate(selectedId);
    },
    'ArrowLeft': () => {
      if (!candidates?.length) return;
      const idx = candidates.findIndex((c) => c.id === selectedId);
      const prev = candidates[Math.max(0, idx - 1)];
      if (prev) setSelectedId(prev.id);
    },
    'ArrowRight': () => {
      if (!candidates?.length) return;
      const idx = candidates.findIndex((c) => c.id === selectedId);
      const next = candidates[Math.min(candidates.length - 1, idx + 1)];
      if (next) setSelectedId(next.id);
    },
    ' ': () => {
      if (selectedId) setPreviewId(selectedId);
    },
    'Escape': () => {
      setSelectedId(null);
      setPreviewId(null);
    },
  }, !!candidates?.length);

  return (
    <div className="space-y-6">
      {/* Pipeline Status */}
      {steps && (
        <PipelineStepper steps={steps} className="mb-8" />
      )}

      {/* WebSocket connection indicator */}
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className={`w-2 h-2 rounded-full ${
          connectionStatus === 'connected' ? 'bg-green-500' :
          connectionStatus === 'reconnecting' ? 'bg-yellow-500' : 'bg-gray-400'
        }`} />
        Pipeline: {connectionStatus}
      </div>

      {/* Candidate Grid */}
      <CandidateGrid
        candidates={candidates || []}
        isLoading={isLoading}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onApprove={(id) => approveMutation.mutate(id)}
        onReject={(id) => rejectMutation.mutate(id)}
        onPreview={setPreviewId}
      />
    </div>
  );
}
```

---

## 9. Performance Optimization Plan

### 9.1 Core Web Vitals Targets

| Metric | Target | Strategy |
|---|---|---|
| **LCP** | < 2.5s | Next.js Image optimization, preload hero images, code splitting |
| **FID** | < 100ms | Minimal JS on server components, dynamic imports for interactivity |
| **CLS** | < 0.1 | Fixed aspect ratios for thumbnails, skeleton loading states |

### 9.2 Specific Optimizations

```typescript
// 1. Dynamic Import for Heavy Components (video player)
import dynamic from 'next/dynamic';

const ClipPlayer = dynamic(
  () => import('@/components/clips/clip-player').then((mod) => mod.ClipPlayer),
  {
    ssr: false,        // Video player uses browser APIs
    loading: () => <div className="aspect-video bg-gray-200 animate-pulse rounded-lg" />,
  }
);

// 2. Next.js Image for all thumbnails
import Image from 'next/image';
// <Image> handles: lazy loading, WebP/AVIF format, responsive sizes, blur placeholder

// 3. React Query staleTime configuration
const queryDefaults = {
  lists: { staleTime: 30_000 },    // Lists change infrequently
  detail: { staleTime: 5_000 },    // Details need fresher data
  analytics: { staleTime: 60_000 }, // Analytics don't need real-time
};

// 4. Virtualized list for large candidate sets
// If candidates.length > 50, use @tanstack/react-virtual
import { useVirtualizer } from '@tanstack/react-virtual';
```

### 9.3 Bundle Optimization

| Technique | Where | Impact |
|---|---|---|
| `next/dynamic` with `ssr: false` | Clip player, chart library | -200KB initial bundle |
| Tree-shaking | All imports (barrel exports) | Variable |
| `@next/bundle-analyzer` | CI pipeline | Monitoring |
| Dynamic imports for modals | Candidate detail view | -50KB on page load |

### 9.4 Image Optimization

```typescript
// All candidate thumbnails use Next.js Image with:
<Image
  src={candidate.thumbnailUrl}
  alt={candidate.summary}
  fill
  className="object-cover"
  sizes="(max-width: 1280px) 33vw, 25vw"  // 4-column grid on desktop
  placeholder="blur"                        // or "empty" for generated thumbnails
  blurDataURL="data:image/jpeg;base64,..."   // 10px preview
/>
```

### 9.5 Caching Strategy

```typescript
// React Query garbage collection: keep inactive queries for 5 min
// This means navigating back to a list is instant if within 5 min
new QueryClient({
  defaultOptions: {
    queries: {
      gcTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// WebSocket updates target specific query keys (NOT full invalidation):
// - 'pipeline.step_update' → invalidate only ['videos', 'detail', videoId]
// - Never invalidate ALL queries on a WebSocket message
```

---

## 10. Implementation Sequence

### Phase 1 — Foundation (Days 1-3)

| Step | Task | Files |
|---|---|---|
| 1.1 | Initialize Next.js 14 with App Router, TypeScript, Tailwind | `npx create-next-app@14` |
| 1.2 | Set up folder structure | All directories |
| 1.3 | Implement primitive UI components | `button.tsx`, `badge.tsx`, `card.tsx`, `input.tsx`, `select.tsx`, `progress-bar.tsx`, `skeleton.tsx`, `tooltip.tsx` |
| 1.4 | Implement API client + types | `api.ts`, `api-types.ts`, `query-keys.ts` |
| 1.5 | Set up Query Provider + devtools | `query-provider.tsx` |
| 1.6 | Create layout shell (sidebar + topbar) | `sidebar.tsx`, `topbar.tsx`, `page-container.tsx` |
| 1.7 | Implement basic routing + redirects | All page files (initially placeholder content) |

### Phase 2 — Upload Flow (Days 4-5)

| Step | Task | Files |
|---|---|---|
| 2.1 | Build UploadZone component | `upload-zone.tsx`, `url-input.tsx`, `upload-progress.tsx` |
| 2.2 | Implement upload page | `upload/page.tsx` |
| 2.3 | Build upload utilities | `upload.ts` |
| 2.4 | Wire up upload API endpoints | Integration test |

### Phase 3 — Pipeline & Review (Days 6-9)

| Step | Task | Files |
|---|---|---|
| 3.1 | Build PipelineStepper | `pipeline-stepper.tsx`, `step-indicator.tsx` |
| 3.2 | Implement WebSocket manager | `websocket.ts` |
| 3.3 | Build usePipeline hook | `use-pipeline.ts` |
| 3.4 | Build CandidateCard + grid | `candidate-card.tsx`, `candidate-grid.tsx`, `score-badge.tsx` |
| 3.5 | Build candidate hooks | `use-candidates.ts` |
| 3.6 | Build keyboard shortcuts hook | `use-keyboard-shortcuts.ts` |
| 3.7 | Implement video detail page (full integration) | `videos/[id]/page.tsx` |
| 3.8 | Build video list page | `videos/page.tsx` |

### Phase 4 — Clips & Analytics (Days 10-12)

| Step | Task | Files |
|---|---|---|
| 4.1 | Build clip cards + list | `clip-list.tsx`, `clip-card.tsx` |
| 4.2 | Build clip player (dynamic import) | `clip-player.tsx` |
| 4.3 | Build clips pages | `clips/page.tsx`, `clips/[id]/page.tsx` |
| 4.4 | Build analytics components | `stats-card.tsx`, `score-chart.tsx`, `overview-panel.tsx` |
| 4.5 | Build analytics hooks + page | `use-analytics.ts`, `analytics/page.tsx` |

### Phase 5 — Settings & Polish (Days 13-15)

| Step | Task | Files |
|---|---|---|
| 5.1 | Build profile form | `profile-form.tsx` |
| 5.2 | Build subtitle style picker | `subtitle-style-picker.tsx` |
| 5.3 | Build settings page | `settings/page.tsx` |
| 5.4 | Add error boundaries throughout | Error boundaries per route segment |
| 5.5 | Accessibility audit | WCAG 2.1 AA compliance check |
| 5.6 | Performance audit | Lighthouse scoring, bundle analysis |

---

## Appendix A: Environment Variables

```bash
# .env.local (V1 development)

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Auth (V1: hardcoded tenant; production: NextAuth.js)
NEXT_PUBLIC_TENANT_ID=dev-tenant-1

# Feature flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_WS_RECONNECT=true
```

## Appendix B: ESLint / Prettier Config

```jsonc
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@tanstack/query/recommended",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }],
    "react/display-name": "off"
  }
}
```

## Appendix C: Tailwind Config Extensions

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      keyframes: {
        'green-flash': {
          '0%': { backgroundColor: 'transparent' },
          '50%': { backgroundColor: 'rgba(34, 197, 94, 0.2)' },
          '100%': { backgroundColor: 'transparent' },
        },
        'red-fade': {
          '0%': { opacity: '1', backgroundColor: 'transparent' },
          '50%': { backgroundColor: 'rgba(239, 68, 68, 0.15)' },
          '100%': { opacity: '0' },
        },
      },
      animation: {
        'green-flash': 'green-flash 0.3s ease-out forwards',
        'red-fade': 'red-fade 0.3s ease-out forwards',
      },
    },
  },
  plugins: [],
};

export default config;
```

---

**Document Status:** Complete ✅  
**Next Steps:** Hand off to developer — begin Phase 1 implementation with `create-next-app@14`.  
**Contract for Backend:** All TypeScript interfaces in `api-types.ts` define the exact API contract. Backend team implements FastAPI endpoints to match these shapes exactly.
