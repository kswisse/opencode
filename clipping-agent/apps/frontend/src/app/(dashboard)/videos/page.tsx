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
