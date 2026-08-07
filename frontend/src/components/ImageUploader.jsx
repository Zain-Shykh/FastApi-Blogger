import { useRef, useState } from 'react'
import ErrorBanner from './ErrorBanner'

export default function ImageUploader({ currentImageUrl, onUpload, onRemove, label = 'Image', hidePreview = false }) {
  const inputRef = useRef(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setError('')
    setBusy(true)
    try {
      await onUpload(file)
    } catch (err) {
      setError(err.detail || err.message)
    } finally {
      setBusy(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  async function handleRemove() {
    setError('')
    setBusy(true)
    try {
      await onRemove()
    } catch (err) {
      setError(err.detail || err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <ErrorBanner message={error} />
      <p className="text-sm font-medium text-slate-700 mb-2">{label}</p>
      {!hidePreview && currentImageUrl && (
        <img src={currentImageUrl} alt="" className="w-full max-w-xs rounded-md mb-2 object-cover" />
      )}
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg"
          disabled={busy}
          onChange={handleFileChange}
          className="text-sm"
        />
        {currentImageUrl && (
          <button
            type="button"
            disabled={busy}
            onClick={handleRemove}
            className="text-sm text-red-600 hover:underline disabled:opacity-50"
          >
            Remove
          </button>
        )}
      </div>
    </div>
  )
}
