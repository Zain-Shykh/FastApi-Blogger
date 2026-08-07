export function PostCardSkeleton() {
  return (
    <div className="rounded-lg border border-slate-200 bg-white overflow-hidden animate-pulse">
      <div className="w-full h-48 bg-slate-200" />
      <div className="p-4 space-y-3">
        <div className="h-5 bg-slate-200 rounded w-3/4" />
        <div className="h-4 bg-slate-100 rounded w-full" />
        <div className="h-4 bg-slate-100 rounded w-5/6" />
      </div>
      <div className="px-4 pb-4 flex items-center justify-between">
        <div className="h-4 bg-slate-100 rounded w-20" />
        <div className="h-4 bg-slate-100 rounded w-24" />
      </div>
    </div>
  )
}

export function PostCardSkeletonGrid({ count = 6 }) {
  return (
    <div className="grid sm:grid-cols-2 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <PostCardSkeleton key={i} />
      ))}
    </div>
  )
}
