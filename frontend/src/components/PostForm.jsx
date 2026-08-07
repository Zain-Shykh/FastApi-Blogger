import { useState } from 'react'
import ErrorBanner from './ErrorBanner'

export default function PostForm({ initialTitle = '', initialContent = '', onSubmit, submitLabel }) {
  const [title, setTitle] = useState(initialTitle)
  const [content, setContent] = useState(initialContent)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await onSubmit({ title, content })
    } catch (err) {
      setError(err.detail || err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorBanner message={error} />
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-slate-700 mb-1">
          Title
        </label>
        <input
          id="title"
          type="text"
          required
          minLength={1}
          maxLength={100}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>
      <div>
        <label htmlFor="content" className="block text-sm font-medium text-slate-700 mb-1">
          Content
        </label>
        <textarea
          id="content"
          required
          minLength={10}
          rows={10}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>
      <button
        type="submit"
        disabled={busy}
        className="px-4 py-2 rounded-md bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
      >
        {busy ? 'Saving…' : submitLabel}
      </button>
    </form>
  )
}
