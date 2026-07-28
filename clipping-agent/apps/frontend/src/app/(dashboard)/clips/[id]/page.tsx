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
