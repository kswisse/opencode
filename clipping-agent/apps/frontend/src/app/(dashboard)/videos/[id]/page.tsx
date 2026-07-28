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
