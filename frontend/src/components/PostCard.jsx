import { Link } from 'react-router-dom'
import { imageUrl } from '../api/client'
import Avatar from './Avatar'

const GRADIENTS = [
  'from-brand-400 to-brand-600',
  'from-violet-400 to-violet-600',
  'from-emerald-400 to-emerald-600',
  'from-amber-400 to-amber-600',
  'from-rose-400 to-rose-600',
]

export default function PostCard({ post }) {
  const gradient = GRADIENTS[post.id % GRADIENTS.length]

  return (
    <article className="rounded-lg border border-slate-200 bg-white overflow-hidden hover:shadow-md hover:-translate-y-0.5 transition-all">
      <Link to={`/posts/${post.id}`} className="block">
        {post.image_file ? (
          <img src={imageUrl(post.image_path)} alt="" className="w-full h-48 object-cover bg-slate-100" />
        ) : (
          <div className={`w-full h-32 bg-gradient-to-br ${gradient} flex items-center justify-center`}>
            <span className="text-3xl font-bold text-white/90">{post.title.slice(0, 1).toUpperCase()}</span>
          </div>
        )}
        <div className="p-4">
          <h2 className="text-lg font-semibold text-slate-900 line-clamp-2">{post.title}</h2>
          <p className="mt-1 text-sm text-slate-600 line-clamp-2">{post.content}</p>
        </div>
      </Link>
      <div className="px-4 pb-4 flex items-center justify-between text-sm text-slate-500">
        <Link to={`/users/${post.author.id}`} className="flex items-center gap-2 hover:text-brand-700 font-medium">
          <Avatar user={post.author} size="sm" />
          {post.author.username}
        </Link>
        <div className="flex items-center gap-3 shrink-0">
          <span>{new Date(post.date_posted).toLocaleDateString()}</span>
          <span>{post.is_liked_by_me ? '♥' : '♡'} {post.likes_count}</span>
          <span>💬 {post.comments_count}</span>
        </div>
      </div>
    </article>
  )
}
