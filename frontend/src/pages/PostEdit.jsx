import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { getPost, updatePost, uploadPostImage, deletePostImage } from '../api/posts'
import { useAuth } from '../context/AuthContext'
import { imageUrl } from '../api/client'
import PostForm from '../components/PostForm'
import ImageUploader from '../components/ImageUploader'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'

export default function PostEdit() {
  const { id } = useParams()
  const { user, token } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [post, setPost] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    getPost(id, token)
      .then((data) => !cancelled && setPost(data))
      .catch((err) => !cancelled && setError(err.detail || err.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [id, token])

  if (loading) return <Spinner />
  if (error) return <ErrorBanner message={error} />
  if (!post) return null

  if (user && user.id !== post.author.id) {
    return <ErrorBanner message="You are not authorized to edit this post." />
  }

  async function handleSubmit({ title, content }) {
    const updated = await updatePost(id, token, { title, content })
    setPost(updated)
    navigate(`/posts/${id}`)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">
        {location.state?.justCreated ? '🎉 Post published — add a thumbnail?' : 'Edit post'}
      </h1>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <ImageUploader
          currentImageUrl={post.image_file ? imageUrl(post.image_path) : null}
          label="Thumbnail"
          onUpload={async (file) => setPost(await uploadPostImage(id, token, file))}
          onRemove={async () => setPost(await deletePostImage(id, token))}
        />
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <PostForm
          initialTitle={post.title}
          initialContent={post.content}
          onSubmit={handleSubmit}
          submitLabel="Save changes"
        />
      </div>
    </div>
  )
}
