import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getPosts } from '../api/posts'
import { useAuth } from '../context/AuthContext'
import PostCard from '../components/PostCard'
import Pagination from '../components/Pagination'
import ErrorBanner from '../components/ErrorBanner'
import EmptyState from '../components/EmptyState'
import Button from '../components/Button'
import { PostCardSkeletonGrid } from '../components/Skeleton'

const LIMIT = 9

export default function Home() {
  const { user, token } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const skip = Number(searchParams.get('skip') || 0)
  const urlSearch = searchParams.get('search') || ''
  const [searchInput, setSearchInput] = useState(urlSearch)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getPosts({ skip, limit: LIMIT, search: urlSearch }, token)
      .then((res) => !cancelled && setData(res))
      .catch((err) => !cancelled && setError(err.detail || err.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [skip, urlSearch, token])

  // debounce search input -> URL param
  useEffect(() => {
    const handle = setTimeout(() => {
      if (searchInput === urlSearch) return
      const next = {}
      if (searchInput) next.search = searchInput
      setSearchParams(next)
    }, 350)
    return () => clearTimeout(handle)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput])

  function handlePageChange(newSkip) {
    const next = { skip: String(newSkip) }
    if (urlSearch) next.search = urlSearch
    setSearchParams(newSkip ? next : (urlSearch ? { search: urlSearch } : {}))
  }

  return (
    <div>
      <section className="mb-10 rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 px-6 py-12 text-center text-white shadow-sm">
        <h1 className="text-3xl sm:text-4xl font-bold">Welcome to FastAPI Blogger</h1>
        <p className="mt-3 text-brand-100 max-w-xl mx-auto">
          Stories, ideas, and updates from the community — built on FastAPI and React.
        </p>
        {!user && (
          <div className="mt-6 flex items-center justify-center gap-3">
            <Button to="/register" variant="inverse">
              Get started
            </Button>
            <Button to="/login" variant="inverseGhost">
              Log in
            </Button>
          </div>
        )}
      </section>

      <div className="flex items-center justify-between gap-4 mb-6">
        <h2 className="text-xl font-bold text-slate-900">
          {urlSearch ? `Results for "${urlSearch}"` : 'Latest posts'}
        </h2>
        <input
          type="search"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search posts…"
          className="w-full max-w-xs rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
      </div>

      <ErrorBanner message={error} />

      {loading && <PostCardSkeletonGrid count={LIMIT} />}

      {!loading && data && data.posts.length === 0 && (
        <EmptyState
          icon={urlSearch ? '🔍' : '📝'}
          title={urlSearch ? 'No posts match your search' : 'No posts yet'}
          description={
            urlSearch
              ? 'Try a different search term.'
              : 'Be the first to share something with the community.'
          }
          action={
            !urlSearch && (
              <Button to={user ? '/posts/new' : '/register'}>
                {user ? 'Write the first post' : 'Sign up to post'}
              </Button>
            )
          }
        />
      )}

      {!loading && data && data.posts.length > 0 && (
        <>
          <div className="grid sm:grid-cols-2 gap-4">
            {data.posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
          <Pagination
            skip={data.skip}
            limit={data.limit}
            total={data.total}
            hasMore={data.has_more}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </div>
  )
}
