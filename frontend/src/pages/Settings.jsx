import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  updateUser,
  changePassword,
  uploadProfilePicture,
  deleteProfilePicture,
  deleteUser,
} from '../api/auth'
import { useAuth } from '../context/AuthContext'
import { imageUrl } from '../api/client'
import ImageUploader from '../components/ImageUploader'
import ErrorBanner from '../components/ErrorBanner'
import Avatar from '../components/Avatar'
import Button from '../components/Button'

function SuccessNote({ message }) {
  if (!message) return null
  return <p className="text-sm text-emerald-600 mb-3">{message}</p>
}

export default function Settings() {
  const { user, token, setUser, logout } = useAuth()
  const navigate = useNavigate()

  const [profileForm, setProfileForm] = useState({ username: user.username, email: user.email })
  const [profileError, setProfileError] = useState('')
  const [profileSuccess, setProfileSuccess] = useState('')
  const [profileBusy, setProfileBusy] = useState(false)

  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '' })
  const [passwordError, setPasswordError] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState('')
  const [passwordBusy, setPasswordBusy] = useState(false)

  async function handleProfileSubmit(e) {
    e.preventDefault()
    setProfileError('')
    setProfileSuccess('')
    setProfileBusy(true)
    try {
      const updated = await updateUser(user.id, token, profileForm)
      setUser(updated)
      setProfileSuccess('Profile updated.')
    } catch (err) {
      setProfileError(err.detail || err.message)
    } finally {
      setProfileBusy(false)
    }
  }

  async function handlePasswordSubmit(e) {
    e.preventDefault()
    setPasswordError('')
    setPasswordSuccess('')
    setPasswordBusy(true)
    try {
      await changePassword(token, passwordForm)
      setPasswordForm({ current_password: '', new_password: '' })
      setPasswordSuccess('Password changed.')
    } catch (err) {
      setPasswordError(err.detail || err.message)
    } finally {
      setPasswordBusy(false)
    }
  }

  async function handleDeleteAccount() {
    if (!window.confirm('Delete your account permanently? This cannot be undone.')) return
    await deleteUser(user.id, token)
    logout()
    navigate('/')
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Settings</h1>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-slate-900 mb-3">Profile picture</h2>
        <div className="flex items-center gap-4">
          <Avatar user={user} size="xl" />
          <div className="flex-1">
            <ImageUploader
              hidePreview
              currentImageUrl={user.image_file ? imageUrl(user.image_path) : null}
              onUpload={async (file) => setUser(await uploadProfilePicture(user.id, token, file))}
              onRemove={async () => setUser(await deleteProfilePicture(user.id, token))}
            />
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-slate-900 mb-3">Profile</h2>
        <form onSubmit={handleProfileSubmit} className="space-y-4">
          <ErrorBanner message={profileError} />
          <SuccessNote message={profileSuccess} />
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-slate-700 mb-1">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={profileForm.username}
              onChange={(e) => setProfileForm((f) => ({ ...f, username: e.target.value }))}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={profileForm.email}
              onChange={(e) => setProfileForm((f) => ({ ...f, email: e.target.value }))}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <Button type="submit" disabled={profileBusy}>
            {profileBusy ? 'Saving…' : 'Save profile'}
          </Button>
        </form>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-slate-900 mb-3">Change password</h2>
        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <ErrorBanner message={passwordError} />
          <SuccessNote message={passwordSuccess} />
          <div>
            <label htmlFor="current_password" className="block text-sm font-medium text-slate-700 mb-1">
              Current password
            </label>
            <input
              id="current_password"
              type="password"
              required
              value={passwordForm.current_password}
              onChange={(e) => setPasswordForm((f) => ({ ...f, current_password: e.target.value }))}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label htmlFor="new_password" className="block text-sm font-medium text-slate-700 mb-1">
              New password
            </label>
            <input
              id="new_password"
              type="password"
              required
              minLength={8}
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm((f) => ({ ...f, new_password: e.target.value }))}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <Button type="submit" disabled={passwordBusy}>
            {passwordBusy ? 'Changing…' : 'Change password'}
          </Button>
        </form>
      </section>

      <section className="rounded-lg border border-red-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-red-700 mb-3">Danger zone</h2>
        <Button variant="danger" onClick={handleDeleteAccount}>
          Delete my account
        </Button>
      </section>
    </div>
  )
}
