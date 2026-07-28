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
