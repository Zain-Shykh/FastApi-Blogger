import { useNavigate } from 'react-router-dom'
import { createPost } from '../api/posts'
import { useAuth } from '../context/AuthContext'
import PostForm from '../components/PostForm'

export default function PostCreate() {
  const { token } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit({ title, content }) {
    const post = await createPost(token, { title, content })
    navigate(`/posts/${post.id}/edit`, { replace: true, state: { justCreated: true } })
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">New post</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <PostForm onSubmit={handleSubmit} submitLabel="Publish" />
      </div>
    </div>
  )
}
