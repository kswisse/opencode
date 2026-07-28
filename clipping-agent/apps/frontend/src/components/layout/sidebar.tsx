'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  { href: '/dashboard/videos', label: 'Videos', icon: '🎬' },
  { href: '/dashboard/clips', label: 'Clips', icon: '✂️' },
  { href: '/dashboard/analytics', label: 'Analytics', icon: '📊' },
  { href: '/dashboard/settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-60 h-screen fixed left-0 top-0 bg-[#0a0a0a] border-r border-[#2a2a2a] flex flex-col z-50">
      <div className="h-16 flex items-center justify-center border-b border-[#2a2a2a]">
        <span className="text-xl font-bold text-[#3b82f6]">Clippy</span>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-[#1c1c1c] text-[#3b82f6]'
                  : 'text-[#a0a0a0] hover:bg-[#141414] hover:text-[#f5f5f5]'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>
      <div className="p-4 border-t border-[#2a2a2a] flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-[#252525] flex items-center justify-center text-sm text-[#a0a0a0]">C</div>
        <span className="text-sm text-[#a0a0a0]">Creator</span>
      </div>
    </aside>
  )
}
