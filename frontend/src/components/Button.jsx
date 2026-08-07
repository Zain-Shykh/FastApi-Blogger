import { Link } from 'react-router-dom'

const base =
  'inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap'

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
}

const variants = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700 shadow-sm',
  secondary: 'border border-slate-300 text-slate-700 bg-white hover:bg-slate-50',
  danger: 'border border-red-300 text-red-700 bg-white hover:bg-red-50',
  warning: 'border border-amber-300 text-amber-800 bg-white hover:bg-amber-100',
  dangerSolid: 'bg-red-600 text-white hover:bg-red-700 shadow-sm',
  ghost: 'text-slate-600 hover:bg-slate-100',
  link: 'text-brand-700 hover:underline p-0',
  // for use on colored/dark backgrounds, e.g. the home page hero
  inverse: 'bg-white text-brand-700 hover:bg-brand-50 shadow-sm',
  inverseGhost: 'text-white border border-white/40 hover:bg-white/10',
}

export default function Button({ variant = 'primary', size = 'md', to, className = '', children, ...props }) {
  const cls = `${base} ${variant === 'link' ? '' : sizes[size]} ${variants[variant]} ${className}`

  if (to) {
    return (
      <Link to={to} className={cls} {...props}>
        {children}
      </Link>
    )
  }

  return (
    <button className={cls} {...props}>
      {children}
    </button>
  )
}
