import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getPost, getPostComments, createComment, deletePost } from '../api/posts'
import { deletePostAsAdmin } from '../api/admin'
import { useAuth } from '../context/AuthContext'
import { imageUrl } from '../api/client'
import LikeButton from '../components/LikeButton'
import CommentForm from '../components/CommentForm'
import CommentThread from '../components/CommentThread'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'
import Avatar from '../components/Avatar'
import Button from '../components/Button'

export default function PostDetail() {
  const { id } = useParams()
  const { user, token } = useAuth()
  const navigate = useNavigate()
  const [post, setPost] = useState(null)
  const [comments, setComments] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const loadComments = useCallback(async () => {
    const [commentsData, postData] = await Promise.all([getPostComments(id), getPost(id, token)])
    setComments(commentsData)
    setPost(postData)
  }, [id, token])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([getPost(id, token), getPostComments(id)])
      .then(([postData, commentsData]) => {
        if (cancelled) return
        setPost(postData)
        setComments(commentsData)
      })
      .catch((err) => !cancelled && setError(err.detail || err.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [id, token])

  async function handleAddComment(content) {
    await createComment(id, token, content)
    await loadComments()
  }

  async function handleDeletePost() {
    if (!window.confirm('Delete this post? This cannot be undone.')) return
    if (isOwner) {
      await deletePost(id, token)
    } else if (user?.is_admin) {
      await deletePostAsAdmin(id, token)
    }
    navigate('/')
  }

  if (loading) return <Spinner />
  if (error) return <ErrorBanner message={error} />
  if (!post) return null

  const isOwner = user && user.id === post.author.id
  const canAdminDelete = user?.is_admin && !isOwner

  return (
    <article>
      {post.image_file && (
        <img src={imageUrl(post.image_path)} alt="" className="w-full max-h-96 object-cover rounded-lg mb-6" />
      )}
      <div className="flex items-start justify-between gap-4">
        <h1 className="text-3xl font-bold text-slate-900">{post.title}</h1>
        {(isOwner || canAdminDelete) && (
          <div className="flex gap-2 shrink-0">
            {isOwner && (
              <Button to={`/posts/${post.id}/edit`} variant="secondary" size="sm">
                Edit
              </Button>
            )}
            <Button variant="danger" size="sm" onClick={handleDeletePost}>
              Delete
            </Button>
          </div>
        )}
      </div>
      <Link to={`/users/${post.author.id}`} className="mt-3 flex items-center gap-2 group w-fit">
        <Avatar user={post.author} size="sm" />
        <span>
          <span className="block text-sm font-medium text-slate-700 group-hover:text-brand-700">
            {post.author.username}
          </span>
          <span className="block text-xs text-slate-400">{new Date(post.date_posted).toLocaleString()}</span>
        </span>
      </Link>
      <div className="prose prose-slate mt-6 whitespace-pre-wrap text-slate-800 leading-relaxed">
        {post.content}
      </div>
      <div className="mt-6 flex items-center gap-3">
        <LikeButton post={post} onChange={(patch) => setPost((p) => ({ ...p, ...patch }))} />
        <span className="text-sm text-slate-500">💬 {post.comments_count} comments</span>
      </div>

      <section className="mt-8 border-t border-slate-200 pt-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Comments</h2>
        {user ? (
          <div className="mb-6">
            <CommentForm onSubmit={handleAddComment} />
          </div>
        ) : (
          <p className="mb-6 text-sm text-slate-500">
            <Link to="/login" className="text-brand-700 hover:underline">
              Log in
            </Link>{' '}
            to leave a comment.
          </p>
        )}
        <CommentThread comments={comments} postId={Number(id)} onChanged={loadComments} />
      </section>
    </article>
  )
}
