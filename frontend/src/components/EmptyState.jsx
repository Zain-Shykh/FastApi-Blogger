export default function EmptyState({ icon = '📝', title, description, action }) {
  return (
    <div className="text-center py-16 px-4 rounded-lg border border-dashed border-slate-300 bg-white">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      {description && <p className="mt-1 text-sm text-slate-500 max-w-sm mx-auto">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
