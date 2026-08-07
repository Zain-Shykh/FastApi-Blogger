export default function Pagination({ skip, limit, total, hasMore, onPageChange }) {
  const currentPage = Math.floor(skip / limit) + 1
  const totalPages = Math.max(1, Math.ceil(total / limit))

  return (
    <div className="flex items-center justify-between mt-6">
      <button
        type="button"
        disabled={skip === 0}
        onClick={() => onPageChange(Math.max(0, skip - limit))}
        className="px-3 py-1.5 rounded-md border border-slate-300 text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100"
      >
        Previous
      </button>
      <span className="text-sm text-slate-500">
        Page {currentPage} of {totalPages}
      </span>
      <button
        type="button"
        disabled={!hasMore}
        onClick={() => onPageChange(skip + limit)}
        className="px-3 py-1.5 rounded-md border border-slate-300 text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100"
      >
        Next
      </button>
    </div>
  )
}
