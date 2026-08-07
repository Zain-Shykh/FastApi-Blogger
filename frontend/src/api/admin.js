import { request } from './client'

export function getMetrics(token) {
  return request('/admin/metrics', { token })
}

export function getTopPosts(token, limit = 5) {
  return request(`/admin/engagement/top-posts?limit=${limit}`, { token })
}

export function toggleUserRole(userId, token) {
  return request(`/admin/users/${userId}/role`, { method: 'PATCH', token })
}

export function banUser(userId, token) {
  return request(`/admin/users/${userId}`, { method: 'DELETE', token })
}

export function deletePostAsAdmin(postId, token) {
  return request(`/admin/posts/${postId}`, { method: 'DELETE', token })
}

export function deleteCommentAsAdmin(commentId, token) {
  return request(`/admin/comments/${commentId}`, { method: 'DELETE', token })
}
