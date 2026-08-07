import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMetrics, getTopPosts, deletePostAsAdmin, toggleUserRole, banUser, listUsers } from '../../api/admin'
import { useAuth } from '../../context/AuthContext'
import Spinner from '../../components/Spinner'
import ErrorBanner from '../../components/ErrorBanner'
import Avatar from '../../components/Avatar'
import Button from '../../components/Button'
import Pagination from '../../components/Pagination'

function MetricCard({ icon, label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="text-2xl">{icon}</div>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  )
}

const USERS_LIMIT = 8

function UserModerationTable({ token, currentUserId }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [skip, setSkip] = useState(0)
  const [busyId, setBusyId] = useState(null)

  function load() {
    setLoading(true)
    listUsers(token, { skip, limit: USERS_LIMIT })
      .then(setData)
      .catch((err) => setError(err.detail || err.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [token, skip]) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleToggleRole(u) {
    setBusyId(u.id)
    setError('')
    try {
      await toggleUserRole(u.id, token)
      setData((d) => ({ ...d, users: d.users.map((x) => (x.id === u.id ? { ...x, is_admin: !x.is_admin } : x)) }))
    } catch (err) {
      setError(err.detail || err.message)
    } finally {
      setBusyId(null)
    }
  }

  async function handleBan(u) {
    if (!window.confirm(`Permanently ban ${u.username}? This deletes their account and content.`)) return
    setBusyId(u.id)
    setError('')
    try {
      await banUser(u.id, token)
      setData((d) => ({ ...d, users: d.users.filter((x) => x.id !== u.id), total: d.total - 1 }))
    } catch (err) {
      setError(err.detail || err.message)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div>
      <ErrorBanner message={error} />
      {loading && <Spinner />}
      {!loading && data && (
        <>
          <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">
                <tr>
                  <th className="px-4 py-2">User</th>
                  <th className="px-4 py-2 hidden sm:table-cell">Email</th>
                  <th className="px-4 py-2">Posts</th>
                  <th className="px-4 py-2">Role</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.users.map((u) => (
                  <tr key={u.id}>
                    <td className="px-4 py-2">
                      <Link to={`/users/${u.id}`} className="flex items-center gap-2 hover:text-brand-700">
                        <Avatar user={u} size="sm" />
                        <span className="font-medium text-slate-900">{u.username}</span>
                      </Link>
                    </td>
                    <td className="px-4 py-2 text-slate-500 hidden sm:table-cell">{u.email}</td>
                    <td className="px-4 py-2 text-slate-500">{u.post_count}</td>
                    <td className="px-4 py-2">
                      {u.is_admin ? (
                        <span className="text-xs font-medium bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
                          admin
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">member</span>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      {u.id === currentUserId ? (
                        <span className="text-xs text-slate-400">you</span>
                      ) : (
                        <div className="flex gap-2 justify-end">
                          <Button
                            variant="warning"
                            size="sm"
                            disabled={busyId === u.id}
                            onClick={() => handleToggleRole(u)}
                          >
                            {u.is_admin ? 'Revoke' : 'Promote'}
                          </Button>
                          <Button variant="danger" size="sm" disabled={busyId === u.id} onClick={() => handleBan(u)}>
                            Ban
                          </Button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            skip={data.skip}
            limit={data.limit}
            total={data.total}
            hasMore={data.has_more}
            onPageChange={setSkip}
          />
        </>
      )}
    </div>
  )
}

export default function AdminDashboard() {
  const { user, token } = useAuth()
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
            <MetricCard icon="👥" label="Users" value={metrics.total_users} />
            <MetricCard icon="🛡️" label="Admins" value={metrics.total_admins} />
            <MetricCard icon="📝" label="Posts" value={metrics.total_posts} />
            <MetricCard icon="💬" label="Comments" value={metrics.total_comments} />
            <MetricCard icon="♥" label="Likes" value={metrics.total_likes} />
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
                    ♥ {post.likes_count} · {new Date(post.date_posted).toLocaleDateString()}
                  </p>
                </div>
                <Button variant="danger" size="sm" onClick={() => handleDeletePost(post.id)}>
                  Delete
                </Button>
              </div>
            ))}
            {topPosts.length === 0 && <p className="p-3 text-sm text-slate-500">No posts yet.</p>}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold text-slate-900 mb-3">User moderation</h2>
        <UserModerationTable token={token} currentUserId={user.id} />
      </section>
    </div>
  )
}
