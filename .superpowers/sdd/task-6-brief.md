# Task 6: Frontend — Next.js Application Shell

**Files to create under `C:\Opencode\clipping-agent\apps\frontend\`:**

### Config
- `package.json`
- `tsconfig.json`
- `next.config.ts`
- `tailwind.config.ts`
- `postcss.config.js`
- `Dockerfile`

### Core App
- `src/app/layout.tsx`
- `src/app/page.tsx`
- `src/app/globals.css`
- `src/providers/query-provider.tsx`

### Library
- `src/lib/api-types.ts`
- `src/lib/api.ts`
- `src/lib/websocket.ts`

### UI Components
- `src/components/ui/button.tsx`
- `src/components/ui/card.tsx`
- `src/components/ui/badge.tsx`
- `src/components/layout/sidebar.tsx`

### Dashboard Layout
- `src/app/(dashboard)/layout.tsx`
- `src/app/(dashboard)/page.tsx`

## File Contents

### package.json
```json
{
  "name": "clippy-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "@tanstack/react-query": "^5.0.0",
    "recharts": "^2.12.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@types/node": "^20.14.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### next.config.ts
```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      { protocol: 'http', hostname: 'localhost', port: '9000' },
      { protocol: 'https', hostname: '**.amazonaws.com' },
    ],
  },
}

export default nextConfig
```

### tailwind.config.ts
```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          0: '#0a0a0a',
          1: '#141414',
          2: '#1c1c1c',
          3: '#252525',
        },
        border: '#2a2a2a',
        accent: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
        },
        success: '#22c55e',
        warning: '#eab308',
        danger: '#ef4444',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
```

### postcss.config.js
```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### Dockerfile
```dockerfile
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=base /app/public ./public
COPY --from=base /app/.next/standalone ./
COPY --from=base /app/.next/static ./.next/static
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
```

### src/app/globals.css
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --surface-0: #0a0a0a;
  --surface-1: #141414;
  --surface-2: #1c1c1c;
  --text-primary: #f5f5f5;
  --text-secondary: #a0a0a0;
  --text-tertiary: #6b6b6b;
  --accent: #3b82f6;
  --border: #2a2a2a;
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--surface-0);
  color: var(--text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

### src/app/layout.tsx
```tsx
import type { Metadata } from 'next'
import './globals.css'
import { QueryProvider } from '@/providers/query-provider'

export const metadata: Metadata = {
  title: 'Clippy - AI Clipping Agent',
  description: 'Automatically detect and generate viral clips from your videos',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
```

### src/app/page.tsx
```tsx
import { redirect } from 'next/navigation'

export default function Home() {
  redirect('/dashboard')
}
```

### src/providers/query-provider.tsx
```tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () => new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 30 * 1000,
          retry: 2,
        },
      },
    })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

### src/lib/api-types.ts
```typescript
export interface Video {
  id: string
  tenant_id: string
  title: string
  source_type: 'youtube' | 'twitch' | 'podcast' | 'local'
  source_url?: string
  status: 'pending' | 'downloading' | 'processing' | 'ready' | 'failed'
  duration_seconds?: number
  file_size_bytes?: number
  thumbnail_url?: string
  metadata: Record<string, unknown>
  error_message?: string
  created_at: string
  updated_at: string
}

export interface PipelineStep {
  name: string
  label: string
  status: 'pending' | 'active' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  error_message?: string
}

export interface ScoreSet {
  virality: number
  retention: number
  hook: number
  emotion: number
  shareability: number
  educational: number
}

export interface ClipCandidate {
  id: string
  video_id: string
  start_time: number
  end_time: number
  duration_seconds: number
  summary: string
  scores: ScoreSet
  predicted_score: number
  status: 'proposed' | 'approved' | 'rejected' | 'generated'
  created_at: string
}

export interface Clip {
  id: string
  candidate_id: string
  video_id: string
  storage_key: string
  duration_seconds?: number
  download_url: string
  created_at: string
}

export interface AnalyticsOverview {
  total_clips: number
  total_views: number
  total_likes: number
  average_completion_rate: number
}

export interface CreatorProfile {
  id: string
  name: string
  brand_colors: { primary: string; secondary: string }
  subtitle_style: { font: string; color: string; position: string; background_opacity: number }
  preferred_duration: number
}
```

### src/lib/api.ts
```typescript
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {}
  if (body) {
    headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    throw new ApiError(res.status, await res.text())
  }
  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, body),
  delete: <T>(path: string) => request<T>('DELETE', path),
}
```

### src/lib/websocket.ts
```typescript
export class PipelineWebSocket {
  private ws: WebSocket | null = null
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  private attempt = 0
  private maxAttempts = 5

  constructor(
    private url: string,
    private onMessage: (data: any) => void,
    private onStatusChange?: (status: 'connected' | 'disconnected' | 'reconnecting') => void,
  ) {}

  connect() {
    this.onStatusChange?.('reconnecting')
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this.attempt = 0
      this.onStatusChange?.('connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.onMessage(data)
      } catch { /* ignore parse errors */ }
    }

    this.ws.onclose = () => {
      this.onStatusChange?.('disconnected')
      this.scheduleReconnect()
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  private scheduleReconnect() {
    if (this.attempt >= this.maxAttempts) return
    const delay = Math.min(1000 * Math.pow(2, this.attempt), 30000)
    this.attempt++
    this.reconnectTimeout = setTimeout(() => this.connect(), delay)
  }

  disconnect() {
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout)
    this.ws?.close()
    this.ws = null
  }
}
```

### UI Components

src/components/ui/button.tsx:
```tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({ variant = 'primary', size = 'md', className = '', children, ...props }: ButtonProps) {
  const base = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none disabled:opacity-50'
  const variants: Record<string, string> = {
    primary: 'bg-[#3b82f6] text-white hover:bg-[#2563eb]',
    secondary: 'bg-[#1c1c1c] text-[#f5f5f5] border border-[#2a2a2a] hover:bg-[#252525]',
    danger: 'bg-[#ef4444]/10 text-[#ef4444] hover:bg-[#ef4444]/20',
    ghost: 'text-[#a0a0a0] hover:text-[#f5f5f5]',
  }
  const sizes: Record<string, string> = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base',
  }
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  )
}
```

src/components/ui/card.tsx:
```tsx
interface CardProps {
  className?: string
  children: React.ReactNode
}

export function Card({ className = '', children }: CardProps) {
  return (
    <div className={`rounded-lg bg-[#141414] border border-[#2a2a2a] ${className}`}>
      {children}
    </div>
  )
}

export function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="p-4 border-b border-[#2a2a2a]">{children}</div>
}

export function CardContent({ children }: { children: React.ReactNode }) {
  return <div className="p-4">{children}</div>
}
```

src/components/ui/badge.tsx:
```tsx
interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger'
  children: React.ReactNode
}

export function Badge({ variant = 'default', children }: BadgeProps) {
  const variants: Record<string, string> = {
    default: 'bg-[#252525] text-[#a0a0a0]',
    success: 'bg-[#22c55e]/10 text-[#22c55e]',
    warning: 'bg-[#eab308]/10 text-[#eab308]',
    danger: 'bg-[#ef4444]/10 text-[#ef4444]',
  }
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${variants[variant]}`}>
      {children}
    </span>
  )
}
```

### src/components/layout/sidebar.tsx
```tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  { href: '/dashboard/videos', label: 'Videos', icon: '🎬' },
  { href: '/dashboard/clips', label: 'Clips', icon: '✂️' },
  { href: '/dashboard/analytics', label: 'Analytics', icon: '📊' },
  { href: '/dashboard/settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-60 h-screen fixed left-0 top-0 bg-[#0a0a0a] border-r border-[#2a2a2a] flex flex-col z-50">
      <div className="h-16 flex items-center justify-center border-b border-[#2a2a2a]">
        <span className="text-xl font-bold text-[#3b82f6]">Clippy</span>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-[#1c1c1c] text-[#3b82f6]'
                  : 'text-[#a0a0a0] hover:bg-[#141414] hover:text-[#f5f5f5]'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>
      <div className="p-4 border-t border-[#2a2a2a] flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-[#252525] flex items-center justify-center text-sm text-[#a0a0a0]">C</div>
        <span className="text-sm text-[#a0a0a0]">Creator</span>
      </div>
    </aside>
  )
}
```

### src/app/(dashboard)/layout.tsx
```tsx
import { Sidebar } from '@/components/layout/sidebar'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Sidebar />
      <main className="ml-60 p-8">{children}</main>
    </div>
  )
}
```

### src/app/(dashboard)/page.tsx
```tsx
import { redirect } from 'next/navigation'

export default function DashboardPage() {
  redirect('/dashboard/videos')
}
```

## Steps

1. Create all files under `C:\Opencode\clipping-agent\apps\frontend\`
2. Run `npm install` from `apps/frontend/`
3. Run `npm run build` — should succeed with no TypeScript errors
4. Verify the build output

## Global Constraints
- Next.js 14 App Router
- TypeScript strict mode
- Tailwind CSS for styling
- TanStack Query for server state only (no Zustand/Redux)
- All file paths use `/` separators
