import { request } from './client'

export function getPosts({ skip = 0, limit } = {}, token) {
  const params = new URLSearchParams({ skip: String(skip) })
  if (limit) params.set('limit', String(limit))
  return request(`/posts?${params.toString()}`, { token })
}

export function getPost(id, token) {
  return request(`/posts/${id}`, { token })
}

export function getPostComments(id) {
  return request(`/posts/${id}/comments`)
}

export function createPost(token, { title, content }) {
  return request('/posts', { method: 'POST', token, body: { title, content } })
}

export function updatePost(id, token, { title, content }) {
  return request(`/posts/${id}`, { method: 'PATCH', token, body: { title, content } })
}

export function deletePost(id, token) {
  return request(`/posts/${id}`, { method: 'DELETE', token })
}

export function uploadPostImage(id, token, file) {
  const form = new FormData()
  form.append('image_file', file)
  return request(`/posts/${id}/image`, { method: 'PATCH', token, body: form, isForm: true })
}

export function deletePostImage(id, token) {
  return request(`/posts/${id}/image`, { method: 'DELETE', token })
}

export function toggleLike(id, token) {
  return request(`/posts/${id}/like`, { method: 'POST', token })
}

export function createComment(postId, token, content) {
  return request(`/posts/${postId}/comments`, { method: 'POST', token, body: { content } })
}

export function deleteComment(postId, commentId, token) {
  return request(`/posts/${postId}/comments/${commentId}`, { method: 'DELETE', token })
}

export function createReply(postId, commentId, token, content) {
  return request(`/posts/${postId}/comments/${commentId}/replies`, {
    method: 'POST',
    token,
    body: { content },
  })
}
