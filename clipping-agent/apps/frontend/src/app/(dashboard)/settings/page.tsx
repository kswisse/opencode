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
