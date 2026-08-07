import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { getUser, getUserPosts } from '../api/auth'
import { toggleUserRole, banUser } from '../api/admin'
import { useAuth } from '../context/AuthContext'
import PostCard from '../components/PostCard'
import Pagination from '../components/Pagination'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'
import EmptyState from '../components/EmptyState'
import Avatar from '../components/Avatar'
import Button from '../components/Button'

const LIMIT = 6

export default function UserProfile() {
  const { id } = useParams()
  const { user: currentUser, token } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const skip = Number(searchParams.get('skip') || 0)

  const [profile, setProfile] = useState(null)
  const [posts, setPosts] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [actionError, setActionError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([getUser(id), getUserPosts(id, { skip, limit: LIMIT }, token)])
      .then(([profileData, postsData]) => {
        if (cancelled) return
        setProfile(profileData)
        setPosts(postsData)
      })
      .catch((err) => !cancelled && setError(err.detail || err.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [id, skip, token])

  async function handleToggleRole() {
    setActionError('')
    try {
      const updated = await toggleUserRole(id, token)
      setProfile((p) => ({ ...p, ...updated }))
    } catch (err) {
      setActionError(err.detail || err.message)
    }
  }

  async function handleBan() {
    if (!window.confirm(`Permanently ban ${profile.username}? This deletes their account and content.`)) return
    setActionError('')
    try {
      await banUser(id, token)
      navigate('/')
    } catch (err) {
      setActionError(err.detail || err.message)
    }
  }

  if (loading) return <Spinner />
  if (error) return <ErrorBanner message={error} />
  if (!profile) return null

  const isSelf = currentUser?.id === profile.id
  const isAdminViewer = currentUser?.is_admin && !isSelf

  return (
    <div>
      <div className="rounded-lg border border-slate-200 bg-white p-6 flex items-center gap-5">
        <Avatar user={profile} size="xl" />
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            {profile.username}
            {profile.is_admin && (
              <span className="text-xs font-medium bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
                admin
              </span>
            )}
          </h1>
          {isSelf && <p className="text-sm text-slate-500">{profile.email}</p>}
          {posts && <p className="mt-1 text-sm text-slate-400">{posts.total} post{posts.total === 1 ? '' : 's'}</p>}
        </div>
      </div>

      {isAdminViewer && (
        <div className="mt-4 p-4 rounded-lg bg-amber-50 border border-amber-200">
          <p className="text-xs font-medium text-amber-800 mb-2">Admin actions</p>
          <ErrorBanner message={actionError} />
          <div className="flex gap-2">
            <Button variant="warning" size="sm" onClick={handleToggleRole}>
              {profile.is_admin ? 'Revoke admin' : 'Make admin'}
            </Button>
            <Button variant="danger" size="sm" onClick={handleBan}>
              Ban user
            </Button>
          </div>
        </div>
      )}

      <h2 className="mt-8 text-lg font-semibold text-slate-900 mb-4">Posts</h2>
      {posts && posts.posts.length === 0 && (
        <EmptyState
          icon="📝"
          title="No posts yet"
          description={isSelf ? "You haven't published anything yet." : `${profile.username} hasn't published anything yet.`}
          action={isSelf && <Button to="/posts/new">Write a post</Button>}
        />
      )}
      {posts && posts.posts.length > 0 && (
        <>
          <div className="grid sm:grid-cols-2 gap-4">
            {posts.posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
          <Pagination
            skip={posts.skip}
            limit={posts.limit}
            total={posts.total}
            hasMore={posts.has_more}
            onPageChange={(newSkip) => setSearchParams(newSkip ? { skip: String(newSkip) } : {})}
          />
        </>
      )}
    </div>
  )
}
