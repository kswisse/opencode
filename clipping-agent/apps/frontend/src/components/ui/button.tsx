interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({ variant = 'primary', size = 'md', className = '', children, ...props }: ButtonProps) {
  const base = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none disabled:opacity-50'
  const variants: Record<string, string> = {
    primary: 'bg-[#3b82f6] text-white hover:bg-[#2563eb]',
    secondary: 'bg-[#1c1c1c] text-[#f5f5f5] border border-[#2a2a2a] hover:bg-[#252525]',
    danger: 'bg-[#ef4444]/10 text-[#ef4444] hover:bg-[#ef4444]/20',
    ghost: 'text-[#a0a0a0] hover:text-[#f5f5f5]',
  }
  const sizes: Record<string, string> = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base',
  }
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  )
}
