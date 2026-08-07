import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getPosts } from '../api/posts'
import { useAuth } from '../context/AuthContext'
import PostCard from '../components/PostCard'
import Pagination from '../components/Pagination'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'

const LIMIT = 9

export default function Home() {
  const { token } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const skip = Number(searchParams.get('skip') || 0)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getPosts({ skip, limit: LIMIT }, token)
      .then((res) => !cancelled && setData(res))
      .catch((err) => !cancelled && setError(err.detail || err.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [skip, token])

  function handlePageChange(newSkip) {
    setSearchParams(newSkip ? { skip: String(newSkip) } : {})
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Latest posts</h1>
      <ErrorBanner message={error} />
      {loading && <Spinner />}
      {!loading && data && data.posts.length === 0 && (
        <p className="text-slate-500">No posts yet.</p>
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
