import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { resetPassword } from '../api/auth'
import ErrorBanner from '../components/ErrorBanner'
import Button from '../components/Button'

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') || ''
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await resetPassword({ token, new_password: newPassword })
      navigate('/login', { replace: true })
    } catch (err) {
      setError(err.detail || err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!token) {
    return <ErrorBanner message="Missing reset token. Use the link from your email." />
  }

  return (
    <div className="max-w-sm mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-6 text-center">Reset password</h1>
      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-6">
        <ErrorBanner message={error} />
        <div>
          <label htmlFor="new_password" className="block text-sm font-medium text-slate-700 mb-1">
            New password
          </label>
          <input
            id="new_password"
            type="password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? 'Resetting…' : 'Reset password'}
        </Button>
      </form>
    </div>
  )
}
