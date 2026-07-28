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
