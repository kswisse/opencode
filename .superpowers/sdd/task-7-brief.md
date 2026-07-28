# Task 7: Frontend Pages — Upload + Videos + Pipeline + Candidates + Clips + Analytics + Settings

Create all page files and interactive components for the Clippy frontend.

## Files to create

### Pages
- `src/app/(dashboard)/upload/page.tsx`
- `src/app/(dashboard)/videos/page.tsx`
- `src/app/(dashboard)/videos/[id]/page.tsx`
- `src/app/(dashboard)/clips/page.tsx`
- `src/app/(dashboard)/clips/[id]/page.tsx`
- `src/app/(dashboard)/analytics/page.tsx`
- `src/app/(dashboard)/settings/page.tsx`

### Components
- `src/components/upload/upload-zone.tsx`
- `src/components/pipeline/pipeline-stepper.tsx`
- `src/components/candidates/candidate-card.tsx`
- `src/components/candidates/score-badge.tsx`

### Hooks
- `src/hooks/use-pipeline.ts`
- `src/hooks/use-candidates.ts`

## Page Contents

### src/app/(dashboard)/upload/page.tsx
```tsx
'use client'

import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { UploadZone } from '@/components/upload/upload-zone'

export default function UploadPage() {
  const router = useRouter()

  const handleFile = async (file: File) => {
    const { id, upload_url } = await api.post<{ id: string; upload_url: string }>('/videos/upload-url')
    if (upload_url) {
      await fetch(upload_url, { method: 'PUT', body: file })
    }
    const video = await api.post('/videos/confirm', {
      storage_key: `raw-videos/${id}.mp4`,
      source_type: 'local',
      metadata: { filename: file.name },
    })
    router.push(`/dashboard/videos/${video.id}`)
  }

  const handleUrl = async (url: string) => {
    const source_type = url.includes('youtube.com') || url.includes('youtu.be') ? 'youtube' : 'twitch'
    const video = await api.post('/videos/confirm', {
      storage_key: url,
      source_type,
      source_url: url,
    })
    router.push(`/dashboard/videos/${video.id}`)
  }

  return (
    <div className="max-w-2xl mx-auto pt-16">
      <h1 className="text-2xl font-semibold text-[#f5f5f5] mb-2">Upload Video</h1>
      <p className="text-sm text-[#6b6b6b] mb-8">
        Drop a video file or paste a YouTube/Twitch URL to start clipping
      </p>
      <UploadZone onFileSelected={handleFile} onUrlSubmit={handleUrl} />
    </div>
  )
}
```

### src/components/upload/upload-zone.tsx
```tsx
'use client'

import { useState, useCallback } from 'react'

interface UploadZoneProps {
  onFileSelected: (file: File) => void
  onUrlSubmit: (url: string) => void
}

export function UploadZone({ onFileSelected, onUrlSubmit }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [url, setUrl] = useState('')
  const [isUploading, setIsUploading] = useState(false)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(e.type === 'dragenter' || e.type === 'dragover')
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('video/')) {
      setIsUploading(true)
      onFileSelected(file)
    }
  }, [onFileSelected])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setIsUploading(true)
      onFileSelected(file)
    }
  }, [onFileSelected])

  return (
    <div className="space-y-6">
      <label
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${
          isDragging ? 'border-[#3b82f6] bg-blue-500/5' : 'border-[#3a3a3a] hover:border-[#5a5a5a]'
        }`}
      >
        <input type="file" accept="video/*" onChange={handleFileInput} className="hidden" />
        <div className="text-3xl mb-4 text-[#a0a0a0]">📁</div>
        {isUploading ? (
          <p className="text-[#3b82f6] font-medium">Uploading...</p>
        ) : (
          <>
            <p className="text-[#f5f5f5] font-medium mb-1">Drop video here or click to browse</p>
            <p className="text-sm text-[#6b6b6b]">MP4, MOV, AVI up to 4GB</p>
          </>
        )}
      </label>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[#2a2a2a]" />
        </div>
        <div className="relative flex justify-center">
          <span className="px-4 text-sm text-[#6b6b6b] bg-[#0a0a0a]">or paste a URL</span>
        </div>
      </div>

      <div className="flex gap-3">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://youtube.com/watch?v=..."
          className="flex-1 h-10 px-3 rounded-md bg-[#1c1c1c] border border-[#2a2a2a] text-sm text-[#f5f5f5] placeholder:text-[#6b6b6b] focus:outline-none focus:border-[#3b82f6]"
        />
        <button
          onClick={() => url && onUrlSubmit(url)}
          disabled={!url}
          className="h-10 px-6 rounded-md bg-[#3b82f6] text-white text-sm font-medium disabled:opacity-50 hover:bg-[#2563eb] transition-colors"
        >
          Import
        </button>
      </div>
    </div>
  )
}
```

### src/app/(dashboard)/videos/page.tsx
```tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Video } from '@/lib/api-types'

const statusColors: Record<string, 'success' | 'warning' | 'danger' | 'default'> = {
  ready: 'success',
  processing: 'warning',
  failed: 'danger',
  pending: 'default',
}

export default function VideosPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['videos'],
    queryFn: () => api.get<{ videos: Video[]; total: number }>('/videos'),
  })

  if (isLoading) return <div className="text-[#a0a0a0]">Loading...</div>

  if (!data?.videos.length) {
    return (
      <div className="text-center pt-24">
        <div className="text-5xl mb-4 text-[#6b6b6b]">🎬</div>
        <h2 className="text-xl font-semibold text-[#f5f5f5] mb-2">No videos yet</h2>
        <p className="text-sm text-[#6b6b6b] mb-6">Upload your first video to start generating clips</p>
        <Link
          href="/dashboard/upload"
          className="inline-flex h-10 px-6 items-center rounded-md bg-[#3b82f6] text-white text-sm font-medium hover:bg-[#2563eb]"
        >
          Upload Video
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#f5f5f5]">Videos</h1>
        <Link
          href="/dashboard/upload"
          className="h-10 px-4 rounded-md bg-[#3b82f6] text-white text-sm font-medium inline-flex items-center hover:bg-[#2563eb]"
        >
          + Upload
        </Link>
      </div>
      <div className="grid gap-4">
        {data.videos.map((video) => (
          <Link key={video.id} href={`/dashboard/videos/${video.id}`}>
            <Card className="p-4 hover:border-[#3b82f6]/50 transition-colors">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-[#f5f5f5]">{video.title || 'Untitled'}</h3>
                  <p className="text-xs text-[#6b6b6b] mt-1">
                    {video.source_type} · {video.duration_seconds ? `${Math.round(video.duration_seconds / 60)} min` : '--'}
                  </p>
                </div>
                <Badge variant={statusColors[video.status] || 'default'}>{video.status}</Badge>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
```

### src/hooks/use-pipeline.ts
```tsx
'use client'

import { useEffect, useState } from 'react'

interface PipelineState {
  steps: Record<string, string>
  status: 'connected' | 'disconnected' | 'reconnecting'
  error: string | null
}

export function usePipeline(videoId: string | undefined): PipelineState {
  const [state, setState] = useState<PipelineState>({
    steps: {},
    status: 'disconnected',
    error: null,
  })

  useEffect(() => {
    if (!videoId) return

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || `ws://localhost:8000/ws/videos/${videoId}`
    let ws: WebSocket
    let reconnectTimer: ReturnType<typeof setTimeout>
    let attempt = 0
    let mounted = true

    function connect() {
      setState(prev => ({ ...prev, status: 'reconnecting' }))
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        if (!mounted) { ws.close(); return }
        attempt = 0
        setState(prev => ({ ...prev, status: 'connected' }))
      }

      ws.onmessage = (event) => {
        if (!mounted) return
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'pipeline.step_update' && data.step_name) {
            setState(prev => ({
              ...prev,
              steps: { ...prev.steps, [data.step_name]: data.step_status },
            }))
          } else if (data.type === 'pipeline.failed' && data.error) {
            setState(prev => ({ ...prev, error: data.error }))
          }
        } catch { /* ignore */ }
      }

      ws.onclose = () => {
        if (!mounted) return
        setState(prev => ({ ...prev, status: 'disconnected' }))
        const delay = Math.min(1000 * Math.pow(2, attempt), 30000)
        attempt++
        reconnectTimer = setTimeout(connect, delay)
      }

      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      mounted = false
      clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, [videoId])

  return state
}
```

### src/components/pipeline/pipeline-stepper.tsx
```tsx
'use client'

interface Step {
  name: string
  status: 'pending' | 'active' | 'completed' | 'failed'
}

interface PipelineStepperProps {
  steps: Step[]
}

const STEP_LABELS: Record<string, string> = {
  download: 'Download',
  transcribe: 'Transcribe',
  analyze: 'Analyze',
  score: 'Score',
  generate: 'Generate',
  done: 'Done',
}

const STEP_ORDER = ['download', 'transcribe', 'analyze', 'score', 'generate', 'done']

export function PipelineStepper({ steps }: PipelineStepperProps) {
  const stepMap = new Map(steps.map(s => [s.name, s.status]))

  return (
    <div className="flex items-center gap-0 w-full">
      {STEP_ORDER.map((name, i) => {
        const status = stepMap.get(name) || 'pending'
        const isLast = i === STEP_ORDER.length - 1

        return (
          <div key={name} className="flex items-center flex-1">
            <div className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-colors ${
                status === 'completed' ? 'bg-[#22c55e] text-white' :
                status === 'active' ? 'bg-[#3b82f6] text-white animate-pulse' :
                status === 'failed' ? 'bg-[#ef4444] text-white' :
                'bg-[#252525] text-[#6b6b6b]'
              }`}>
                {status === 'completed' ? '✓' : status === 'failed' ? '✗' : i + 1}
              </div>
              <span className={`text-xs whitespace-nowrap ${
                status === 'completed' ? 'text-[#22c55e]' :
                status === 'active' ? 'text-[#3b82f6]' :
                status === 'failed' ? 'text-[#ef4444]' :
                'text-[#6b6b6b]'
              }`}>
                {STEP_LABELS[name]}
              </span>
            </div>
            {!isLast && (
              <div className={`flex-1 h-0.5 mx-2 ${
                status === 'completed' ? 'bg-[#22c55e]' : 'bg-[#2a2a2a]'
              }`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
```

### src/components/candidates/score-badge.tsx
```tsx
interface ScoreBadgeProps {
  label: string
  value: number
}

export function ScoreBadge({ label, value }: ScoreBadgeProps) {
  const color = value >= 85 ? '#22c55e' : value >= 70 ? '#eab308' : '#ef4444'

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold"
      style={{ backgroundColor: `${color}18`, color }}
    >
      {Math.round(value)}
      <span className="opacity-70 font-normal">{label}</span>
    </span>
  )
}
```

### src/components/candidates/candidate-card.tsx
```tsx
import type { ClipCandidate } from '@/lib/api-types'
import { ScoreBadge } from './score-badge'

interface CandidateCardProps {
  candidate: ClipCandidate
  onApprove: (id: string) => void
  onReject: (id: string) => void
}

export function CandidateCard({ candidate, onApprove, onReject }: CandidateCardProps) {
  const topScores = Object.entries(candidate.scores)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3)

  return (
    <div className="rounded-lg bg-[#141414] border border-[#2a2a2a] overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all">
      <div className="relative aspect-video bg-[#1c1c1c] flex items-center justify-center text-[#6b6b6b] text-sm">
        <span>▶ {Math.round(candidate.duration_seconds)}s</span>
        <span className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/70 text-xs text-white">
          {Math.round(candidate.end_time - candidate.start_time)}s
        </span>
      </div>
      <div className="p-3 space-y-2">
        <p className="text-sm text-[#f5f5f5] line-clamp-1">{candidate.summary || 'No preview available'}</p>
        <div className="flex flex-wrap gap-1">
          {topScores.map(([key, value]) => (
            <ScoreBadge key={key} label={key} value={value} />
          ))}
        </div>
        <div className="flex gap-2 pt-2 border-t border-[#2a2a2a]">
          <button
            onClick={() => onApprove(candidate.id)}
            className="flex-1 h-9 rounded-md bg-[#22c55e]/10 text-[#22c55e] text-sm font-medium hover:bg-[#22c55e]/20 transition-colors"
          >
            Approve
          </button>
          <button
            onClick={() => onReject(candidate.id)}
            className="flex-1 h-9 rounded-md border border-[#ef4444]/30 text-[#ef4444] text-sm font-medium hover:bg-[#ef4444]/10 transition-colors"
          >
            Reject
          </button>
        </div>
      </div>
    </div>
  )
}
```

### src/app/(dashboard)/videos/[id]/page.tsx
```tsx
'use client'

import { useParams } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { PipelineStepper } from '@/components/pipeline/pipeline-stepper'
import { CandidateCard } from '@/components/candidates/candidate-card'
import { usePipeline } from '@/hooks/use-pipeline'
import { Button } from '@/components/ui/button'
import type { PipelineStep } from '@/lib/api-types'

export default function VideoDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['video', id],
    queryFn: () => api.get<{ video: any; pipeline: PipelineStep[] }>(`/videos/${id}`),
  })

  const { data: candidatesData } = useQuery({
    queryKey: ['candidates', id],
    queryFn: () => api.get<{ candidates: any[] }>(`/candidates/video/${id}`),
    enabled: data?.video?.status === 'ready',
  })

  const pipelineWs = usePipeline(data?.video?.status !== 'ready' ? id : undefined)

  const approveMutation = useMutation({
    mutationFn: (candidateId: string) => api.post(`/candidates/${candidateId}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates', id] })
      queryClient.invalidateQueries({ queryKey: ['clips'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: (candidateId: string) => api.post(`/candidates/${candidateId}/reject`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['candidates', id] }),
  })

  if (isLoading) return <div className="text-[#a0a0a0]">Loading...</div>
  if (!data) return <div className="text-[#ef4444]">Video not found</div>

  const { video, pipeline } = data

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-[#f5f5f5]">{video.title || 'Untitled Video'}</h1>
        <p className="text-sm text-[#6b6b6b] mt-1">
          {video.source_type} · {video.duration_seconds ? `${Math.round(video.duration_seconds / 60)} min` : '--'}
        </p>
      </div>

      <div className="bg-[#141414] rounded-lg border border-[#2a2a2a] p-4">
        <PipelineStepper steps={pipeline?.length ? pipeline : []} />
      </div>

      {pipelineWs.status === 'connected' && (
        <div className="text-xs text-[#22c55e] flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#22c55e] animate-pulse" />
          Pipeline live
        </div>
      )}

      {pipelineWs.error && (
        <div className="text-xs text-[#ef4444] bg-[#ef4444]/10 rounded-md p-3">
          Pipeline error: {pipelineWs.error}
        </div>
      )}

      {candidatesData && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-[#f5f5f5]">
            Clip Candidates ({candidatesData.candidates.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {candidatesData.candidates.map((candidate: any) => (
              <CandidateCard
                key={candidate.id}
                candidate={candidate}
                onApprove={(id) => approveMutation.mutate(id)}
                onReject={(id) => rejectMutation.mutate(id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
```

### src/app/(dashboard)/clips/page.tsx
```tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/card'

export default function ClipsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['clips'],
    queryFn: () => api.get<{ clips: any[] }>('/clips'),
  })

  if (isLoading) return <div className="text-[#a0a0a0]">Loading...</div>

  if (!data?.clips.length) {
    return (
      <div className="text-center pt-24">
        <div className="text-5xl mb-4 text-[#6b6b6b]">✂️</div>
        <h2 className="text-xl font-semibold text-[#f5f5f5] mb-2">No clips yet</h2>
        <p className="text-sm text-[#6b6b6b]">Upload a video and approve candidates to generate clips</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[#f5f5f5]">Clips</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.clips.map((clip: any) => (
          <Link key={clip.id} href={`/dashboard/clips/${clip.id}`}>
            <Card className="p-4 hover:border-[#3b82f6]/50 transition-colors">
              <div className="aspect-video bg-[#1c1c1c] rounded-md mb-2 flex items-center justify-center text-[#6b6b6b] text-sm">
                ▶ {clip.duration_seconds ? `${Math.round(clip.duration_seconds)}s` : '--'}
              </div>
              <p className="text-xs text-[#6b6b6b]">
                {clip.resolution || '1080x1920'} · {clip.file_format || 'mp4'}
              </p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
```

### src/app/(dashboard)/clips/[id]/page.tsx
```tsx
'use client'

import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'

export default function ClipDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data, isLoading } = useQuery({
    queryKey: ['clip', id],
    queryFn: () => api.get<{ clip: any }>(`/clips/${id}`),
  })

  if (isLoading) return <div className="text-[#a0a0a0]">Loading...</div>
  if (!data) return <div className="text-[#ef4444]">Clip not found</div>

  const { clip } = data

  return (
    <div className="space-y-6">
      <div className="aspect-video bg-black rounded-lg flex items-center justify-center text-[#6b6b6b] max-w-2xl mx-auto">
        <div className="text-center">
          <div className="text-4xl mb-2">▶</div>
          <p className="text-sm">Clip Preview</p>
          {clip.duration_seconds && <p className="text-xs mt-1">{Math.round(clip.duration_seconds)}s</p>}
        </div>
      </div>
      <div className="flex gap-3 justify-center">
        <Button onClick={() => window.open(clip.download_url, '_blank')} disabled={!clip.download_url}>
          Download
        </Button>
        <Button variant="secondary">Share</Button>
      </div>
    </div>
  )
}
```

### src/app/(dashboard)/analytics/page.tsx
```tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: () => api.get<{
      total_clips: number
      total_views: number
      total_likes: number
      total_shares: number
      average_completion_rate: number
    }>('/analytics/overview'),
  })

  if (isLoading) return <div className="text-[#a0a0a0]">Loading...</div>

  const stats = [
    { label: 'Total Clips', value: data?.total_clips ?? 0 },
    { label: 'Total Views', value: data?.total_views ?? 0 },
    { label: 'Total Likes', value: data?.total_likes ?? 0 },
    { label: 'Avg Completion', value: data?.average_completion_rate ? `${(data.average_completion_rate * 100).toFixed(0)}%` : '0%' },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[#f5f5f5]">Analytics</h1>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent>
              <p className="text-sm text-[#6b6b6b] uppercase tracking-wide">{stat.label}</p>
              <p className="text-2xl font-bold text-[#f5f5f5] mt-1">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
```

### src/app/(dashboard)/settings/page.tsx
```tsx
'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useState } from 'react'
import type { CreatorProfile } from '@/lib/api-types'

export default function SettingsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: () => api.get<CreatorProfile>('/profile'),
  })

  if (isLoading) return <div className="text-[#a0a0a0]">Loading...</div>
  if (!data) return <div className="text-[#a0a0a0]">Settings not available</div>

  return (
    <div className="space-y-6 max-w-xl">
      <h1 className="text-xl font-semibold text-[#f5f5f5]">Settings</h1>
      <Card>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm text-[#6b6b6b] block mb-1">Name</label>
            <input
              defaultValue={data.name}
              className="w-full h-10 px-3 rounded-md bg-[#1c1c1c] border border-[#2a2a2a] text-sm text-[#f5f5f5]"
            />
          </div>
          <div>
            <label className="text-sm text-[#6b6b6b] block mb-1">Subtitle Font</label>
            <input
              defaultValue={data.subtitle_style.font}
              className="w-full h-10 px-3 rounded-md bg-[#1c1c1c] border border-[#2a2a2a] text-sm text-[#f5f5f5]"
            />
          </div>
          <div>
            <label className="text-sm text-[#6b6b6b] block mb-1">Preferred Clip Duration (seconds)</label>
            <input
              type="number"
              defaultValue={data.preferred_duration}
              className="w-full h-10 px-3 rounded-md bg-[#1c1c1c] border border-[#2a2a2a] text-sm text-[#f5f5f5]"
            />
          </div>
          <Button>Save Changes</Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

### src/hooks/use-candidates.ts
```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useCandidates(videoId: string) {
  const queryClient = useQueryClient()

  const approve = useMutation({
    mutationFn: (candidateId: string) => api.post(`/candidates/${candidateId}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates', videoId] })
      queryClient.invalidateQueries({ queryKey: ['clips'] })
    },
  })

  const reject = useMutation({
    mutationFn: (candidateId: string) => api.post(`/candidates/${candidateId}/reject`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['candidates', videoId] }),
  })

  return { approve, reject }
}
```

## Steps

1. Create all files under the correct paths in `C:\Opencode\clipping-agent\apps\frontend\`
2. Run `npm run build` — must succeed with zero errors
3. If there are TypeScript errors, fix them

## Global Constraints
- Next.js 14 App Router
- TypeScript strict mode
- Tailwind CSS
- TanStack Query for server state
- All API calls through `@/lib/api` client
