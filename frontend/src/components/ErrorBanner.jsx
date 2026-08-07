export default function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div className="rounded-md bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 mb-4">
      {message}
    </div>
  )
}
