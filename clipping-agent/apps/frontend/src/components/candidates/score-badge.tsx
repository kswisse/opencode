interface ScoreBadgeProps {
  label: string
  value: number
}

export function ScoreBadge({ label, value }: ScoreBadgeProps) {
  const color = value >= 85 ? '#22c55e' : value >= 70 ? '#eab308' : '#ef4444'

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold"
      style={{ backgroundColor: `${color}18`, color }}
    >
      {Math.round(value)}
      <span className="opacity-70 font-normal">{label}</span>
    </span>
  )
}
