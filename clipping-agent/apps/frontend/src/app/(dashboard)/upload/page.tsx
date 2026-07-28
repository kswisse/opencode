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
    const video = await api.post<{ id: string }>('/videos/confirm', {
      storage_key: `raw-videos/${id}.mp4`,
      source_type: 'local',
      metadata: { filename: file.name },
    })
    router.push(`/dashboard/videos/${video.id}`)
  }

  const handleUrl = async (url: string) => {
    const source_type = url.includes('youtube.com') || url.includes('youtu.be') ? 'youtube' : 'twitch'
    const video = await api.post<{ id: string }>('/videos/confirm', {
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
