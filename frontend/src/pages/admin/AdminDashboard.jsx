import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMetrics, getTopPosts, deletePostAsAdmin, toggleUserRole, banUser } from '../../api/admin'
import { getUser } from '../../api/auth'
import { useAuth } from '../../context/AuthContext'
import Spinner from '../../components/Spinner'
import ErrorBanner from '../../components/ErrorBanner'

function MetricCard({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
    </div>
  )
}

function UserLookup({ token }) {
  const [userId, setUserId] = useState('')
  const [foundUser, setFoundUser] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleLookup(e) {
    e.preventDefault()
    setError('')
    setFoundUser(null)
    setBusy(true)
    try {
      const data = await getUser(userId)
      setFoundUser(data)
    } catch (err) {
      setError(err.detail || err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleToggleRole() {
    setError('')
    try {
      const updated = await toggleUserRole(foundUser.id, token)
      setFoundUser((u) => ({ ...u, ...updated }))
    } catch (err) {
      setError(err.detail || err.message)
    }
  }

  async function handleBan() {
    if (!window.confirm(`Permanently ban ${foundUser.username}?`)) return
    setError('')
    try {
      await banUser(foundUser.id, token)
      setFoundUser(null)
      setUserId('')
    } catch (err) {
      setError(err.detail || err.message)
    }
  }

  return (
    <div>
      <form onSubmit={handleLookup} className="flex gap-2 mb-3">
        <input
          type="number"
          placeholder="User ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          required
          className="rounded-md border border-slate-300 px-3 py-2 text-sm w-32"
        />
        <button
          type="submit"
          disabled={busy}
          className="px-3 py-2 rounded-md bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
        >
          Look up
        </button>
      </form>
      <ErrorBanner message={error} />
      {foundUser && (
        <div className="flex items-center justify-between rounded-md border border-slate-200 p-3">
          <div>
            <Link to={`/users/${foundUser.id}`} className="font-medium text-slate-900 hover:text-brand-700">
              {foundUser.username}
            </Link>
            <span className="ml-2 text-xs text-slate-500">{foundUser.is_admin ? 'admin' : 'member'}</span>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleToggleRole}
              className="px-3 py-1.5 rounded-md border border-slate-300 text-sm hover:bg-slate-100"
            >
              {foundUser.is_admin ? 'Revoke admin' : 'Make admin'}
            </button>
            <button
              type="button"
              onClick={handleBan}
              className="px-3 py-1.5 rounded-md border border-red-300 text-red-700 text-sm hover:bg-red-50"
            >
              Ban
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function AdminDashboard() {
  const { token } = useAuth()
  const [metrics, setMetrics] = useState(null)
  const [topPosts, setTopPosts] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    Promise.all([getMetrics(token), getTopPosts(token)])
      .then(([metricsData, topPostsData]) => {
        if (cancelled) return
        setMetrics(metricsData)
        setTopPosts(topPostsData)
      })
      .catch((err) => !cancelled && setError(err.detail || err.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [token])

  async function handleDeletePost(postId) {
    if (!window.confirm('Delete this post?')) return
    await deletePostAsAdmin(postId, token)
    setTopPosts((posts) => posts.filter((p) => p.id !== postId))
  }

  if (loading) return <Spinner />

  return (
    <div className="space-y-10">
      <h1 className="text-2xl font-bold text-slate-900">Admin dashboard</h1>
      <ErrorBanner message={error} />

      {metrics && (
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-3">Platform metrics</h2>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <MetricCard label="Users" value={metrics.total_users} />
            <MetricCard label="Admins" value={metrics.total_admins} />
            <MetricCard label="Posts" value={metrics.total_posts} />
            <MetricCard label="Comments" value={metrics.total_comments} />
            <MetricCard label="Likes" value={metrics.total_likes} />
          </div>
        </section>
      )}

      {topPosts && (
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-3">Top posts by likes</h2>
          <div className="rounded-lg border border-slate-200 bg-white divide-y divide-slate-100">
            {topPosts.map((post) => (
              <div key={post.id} className="flex items-center justify-between p-3">
                <div>
                  <Link to={`/posts/${post.id}`} className="font-medium text-slate-900 hover:text-brand-700">
                    {post.title}
                  </Link>
                  <p className="text-xs text-slate-500">
                    {post.likes_count} likes · {new Date(post.date_posted).toLocaleDateString()}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleDeletePost(post.id)}
                  className="px-3 py-1.5 rounded-md border border-red-300 text-red-700 text-sm hover:bg-red-50"
                >
                  Delete
                </button>
              </div>
            ))}
            {topPosts.length === 0 && <p className="p-3 text-sm text-slate-500">No posts yet.</p>}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold text-slate-900 mb-3">User moderation</h2>
        <p className="text-sm text-slate-500 mb-3">
          Look up a user by ID to promote, demote, or ban them. (You can also moderate a user directly from
          their profile page.)
        </p>
        <UserLookup token={token} />
      </section>
    </div>
  )
}
