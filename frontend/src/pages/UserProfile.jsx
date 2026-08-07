import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { getUser, getUserPosts } from '../api/auth'
import { toggleUserRole, banUser } from '../api/admin'
import { useAuth } from '../context/AuthContext'
import { imageUrl } from '../api/client'
import PostCard from '../components/PostCard'
import Pagination from '../components/Pagination'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'

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
      <div className="flex items-center gap-4">
        <img
          src={imageUrl(profile.image_path)}
          alt=""
          className="h-16 w-16 rounded-full object-cover bg-slate-200"
          onError={(e) => {
            e.currentTarget.style.visibility = 'hidden'
          }}
        />
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{profile.username}</h1>
          <p className="text-sm text-slate-500">{isSelf ? profile.email : ''}</p>
        </div>
      </div>

      {isAdminViewer && (
        <div className="mt-4 p-3 rounded-md bg-amber-50 border border-amber-200">
          <p className="text-xs font-medium text-amber-800 mb-2">Admin actions</p>
          <ErrorBanner message={actionError} />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleToggleRole}
              className="px-3 py-1.5 rounded-md border border-amber-300 text-sm text-amber-800 hover:bg-amber-100"
            >
              {profile.is_admin ? 'Revoke admin' : 'Make admin'}
            </button>
            <button
              type="button"
              onClick={handleBan}
              className="px-3 py-1.5 rounded-md border border-red-300 text-sm text-red-700 hover:bg-red-50"
            >
              Ban user
            </button>
          </div>
        </div>
      )}

      <h2 className="mt-8 text-lg font-semibold text-slate-900 mb-4">Posts</h2>
      {posts && posts.posts.length === 0 && <p className="text-slate-500">No posts yet.</p>}
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
