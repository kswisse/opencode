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
