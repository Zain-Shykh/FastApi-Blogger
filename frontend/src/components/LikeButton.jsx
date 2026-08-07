import { useState } from 'react'
import { toggleLike } from '../api/posts'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

export default function LikeButton({ post, onChange }) {
  const { token, user } = useAuth()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)

  async function handleClick() {
    if (!user) {
      navigate('/login')
      return
    }
    setBusy(true)
    try {
      await toggleLike(post.id, token)
      onChange({
        is_liked_by_me: !post.is_liked_by_me,
        likes_count: post.likes_count + (post.is_liked_by_me ? -1 : 1),
      })
    } finally {
      setBusy(false)
    }
  }

  return (
    <button
      type="button"
      disabled={busy}
      onClick={handleClick}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-sm font-medium transition-colors ${
        post.is_liked_by_me
          ? 'bg-red-50 border-red-200 text-red-600'
          : 'border-slate-300 text-slate-600 hover:bg-slate-100'
      }`}
    >
      <span>{post.is_liked_by_me ? '♥' : '♡'}</span>
      <span>{post.likes_count}</span>
    </button>
  )
}
