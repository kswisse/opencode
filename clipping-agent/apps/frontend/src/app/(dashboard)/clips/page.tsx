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
