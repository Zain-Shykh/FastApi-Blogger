import { Link } from 'react-router-dom'
import { imageUrl } from '../api/client'

export default function PostCard({ post }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white overflow-hidden hover:shadow-md transition-shadow">
      <Link to={`/posts/${post.id}`} className="block">
        {post.image_path && (
          <img
            src={imageUrl(post.image_path)}
            alt=""
            className="w-full h-48 object-cover bg-slate-100"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        )}
        <div className="p-4">
          <h2 className="text-lg font-semibold text-slate-900 line-clamp-2">{post.title}</h2>
          <p className="mt-1 text-sm text-slate-600 line-clamp-2">{post.content}</p>
        </div>
      </Link>
      <div className="px-4 pb-4 flex items-center justify-between text-sm text-slate-500">
        <Link to={`/users/${post.author.id}`} className="hover:text-brand-700 font-medium">
          {post.author.username}
        </Link>
        <div className="flex items-center gap-3">
          <span>{new Date(post.date_posted).toLocaleDateString()}</span>
          <span>♥ {post.likes_count}</span>
          <span>💬 {post.comments_count}</span>
        </div>
      </div>
    </article>
  )
}
