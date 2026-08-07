import { useState } from 'react'
import { imageUrl } from '../api/client'

const PALETTE = [
  'bg-rose-500', 'bg-orange-500', 'bg-amber-500', 'bg-emerald-500',
  'bg-teal-500', 'bg-cyan-500', 'bg-blue-500', 'bg-indigo-500',
  'bg-violet-500', 'bg-fuchsia-500', 'bg-pink-500',
]

const SIZES = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-16 w-16 text-xl',
  xl: 'h-24 w-24 text-3xl',
}

function initials(username) {
  if (!username) return '?'
  const parts = username.trim().split(/[\s_-]+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return username.slice(0, 2).toUpperCase()
}

function colorFor(id) {
  const n = typeof id === 'number' ? id : Math.abs(String(id ?? '').split('').reduce((a, c) => a + c.charCodeAt(0), 0))
  return PALETTE[n % PALETTE.length]
}

export default function Avatar({ user, size = 'md', className = '' }) {
  const [broken, setBroken] = useState(false)
  const sizeClasses = SIZES[size] || SIZES.md
  const src = user?.image_file ? imageUrl(user.image_path) : null

  if (src && !broken) {
    return (
      <img
        src={src}
        alt=""
        onError={() => setBroken(true)}
        className={`${sizeClasses} rounded-full object-cover shrink-0 ${className}`}
      />
    )
  }

  return (
    <div
      className={`${sizeClasses} ${colorFor(user?.id)} rounded-full shrink-0 flex items-center justify-center font-semibold text-white select-none ${className}`}
    >
      {initials(user?.username)}
    </div>
  )
}
