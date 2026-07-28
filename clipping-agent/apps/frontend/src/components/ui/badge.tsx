interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger'
  children: React.ReactNode
}

export function Badge({ variant = 'default', children }: BadgeProps) {
  const variants: Record<string, string> = {
    default: 'bg-[#252525] text-[#a0a0a0]',
    success: 'bg-[#22c55e]/10 text-[#22c55e]',
    warning: 'bg-[#eab308]/10 text-[#eab308]',
    danger: 'bg-[#ef4444]/10 text-[#ef4444]',
  }
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${variants[variant]}`}>
      {children}
    </span>
  )
}
