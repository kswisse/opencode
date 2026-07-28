'use client'

interface Step {
  name: string
  status: 'pending' | 'active' | 'completed' | 'failed'
}

interface PipelineStepperProps {
  steps: Step[]
}

const STEP_LABELS: Record<string, string> = {
  download: 'Download',
  transcribe: 'Transcribe',
  analyze: 'Analyze',
  score: 'Score',
  generate: 'Generate',
  done: 'Done',
}

const STEP_ORDER = ['download', 'transcribe', 'analyze', 'score', 'generate', 'done']

export function PipelineStepper({ steps }: PipelineStepperProps) {
  const stepMap = new Map(steps.map(s => [s.name, s.status]))

  return (
    <div className="flex items-center gap-0 w-full">
      {STEP_ORDER.map((name, i) => {
        const status = stepMap.get(name) || 'pending'
        const isLast = i === STEP_ORDER.length - 1

        return (
          <div key={name} className="flex items-center flex-1">
            <div className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-colors ${
                status === 'completed' ? 'bg-[#22c55e] text-white' :
                status === 'active' ? 'bg-[#3b82f6] text-white animate-pulse' :
                status === 'failed' ? 'bg-[#ef4444] text-white' :
                'bg-[#252525] text-[#6b6b6b]'
              }`}>
                {status === 'completed' ? '✓' : status === 'failed' ? '✗' : i + 1}
              </div>
              <span className={`text-xs whitespace-nowrap ${
                status === 'completed' ? 'text-[#22c55e]' :
                status === 'active' ? 'text-[#3b82f6]' :
                status === 'failed' ? 'text-[#ef4444]' :
                'text-[#6b6b6b]'
              }`}>
                {STEP_LABELS[name]}
              </span>
            </div>
            {!isLast && (
              <div className={`flex-1 h-0.5 mx-2 ${
                status === 'completed' ? 'bg-[#22c55e]' : 'bg-[#2a2a2a]'
              }`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
