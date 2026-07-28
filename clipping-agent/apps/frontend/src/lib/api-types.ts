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
