import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { createReply, deleteComment } from '../api/posts'
import { deleteCommentAsAdmin } from '../api/admin'
import CommentForm from './CommentForm'
import ErrorBanner from './ErrorBanner'

function CommentItem({ comment, postId, onChanged, depth = 0 }) {
  const { user, token } = useAuth()
  const [replying, setReplying] = useState(false)
  const [error, setError] = useState('')

  const isOwner = user && user.id === comment.user.id
  const canAdminDelete = user && user.is_admin && !isOwner

  async function handleReply(content) {
    await createReply(postId, comment.id, token, content)
    setReplying(false)
    onChanged()
  }

  async function handleDelete() {
    setError('')
    try {
      if (isOwner) {
        await deleteComment(postId, comment.id, token)
      } else if (canAdminDelete) {
        await deleteCommentAsAdmin(comment.id, token)
      }
      onChanged()
    } catch (err) {
      setError(err.detail || err.message)
    }
  }

  return (
    <div className={depth > 0 ? 'pl-6 border-l border-slate-200' : ''}>
      <div className="py-3">
        <ErrorBanner message={error} />
        <div className="flex items-center gap-2 text-sm">
          <Link to={`/users/${comment.user.id}`} className="font-medium text-slate-900 hover:text-brand-700">
            {comment.user.username}
          </Link>
          <span className="text-slate-400">{new Date(comment.date_posted).toLocaleString()}</span>
        </div>
        <p className="mt-1 text-sm text-slate-700 whitespace-pre-wrap">{comment.content}</p>
        <div className="mt-1 flex items-center gap-3 text-xs">
          {user && (
            <button
              type="button"
              onClick={() => setReplying((v) => !v)}
              className="text-slate-500 hover:text-brand-700 font-medium"
            >
              Reply
            </button>
          )}
          {(isOwner || canAdminDelete) && (
            <button type="button" onClick={handleDelete} className="text-red-500 hover:text-red-700 font-medium">
              Delete
            </button>
          )}
        </div>
        {replying && (
          <div className="mt-2">
            <CommentForm
              onSubmit={handleReply}
              placeholder={`Reply to ${comment.user.username}…`}
              submitLabel="Reply"
              autoFocus
              onCancel={() => setReplying(false)}
            />
          </div>
        )}
      </div>
      {comment.replies?.length > 0 && (
        <div>
          {comment.replies.map((reply) => (
            <CommentItem key={reply.id} comment={reply} postId={postId} onChanged={onChanged} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function CommentThread({ comments, postId, onChanged }) {
  if (!comments.length) {
    return <p className="text-sm text-slate-500 py-4">No comments yet. Be the first to comment.</p>
  }

  return (
    <div className="divide-y divide-slate-100">
      {comments.map((comment) => (
        <CommentItem key={comment.id} comment={comment} postId={postId} onChanged={onChanged} />
      ))}
    </div>
  )
}
