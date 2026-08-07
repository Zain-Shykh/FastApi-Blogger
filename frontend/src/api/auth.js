import { request } from './client'

export function register({ username, email, password }) {
  return request('/users', { method: 'POST', body: { username, email, password } })
}

export async function login({ email, password }) {
  const data = await request('/users/token', {
    method: 'POST',
    isUrlEncoded: true,
    body: { username: email, password },
  })
  return data.access_token
}

export function getMe(token) {
  return request('/users/me', { token })
}

export function getUser(userId) {
  return request(`/users/${userId}`)
}

export function updateUser(userId, token, data) {
  return request(`/users/${userId}`, { method: 'PATCH', token, body: data })
}

export function deleteUser(userId, token) {
  return request(`/users/${userId}`, { method: 'DELETE', token })
}

export function getUserPosts(userId, { skip = 0, limit } = {}, token) {
  const params = new URLSearchParams({ skip: String(skip) })
  if (limit) params.set('limit', String(limit))
  return request(`/users/${userId}/posts?${params.toString()}`, { token })
}

export function forgotPassword(email) {
  return request('/users/forgot-password', { method: 'POST', body: { email } })
}

export function resetPassword({ token, new_password }) {
  return request('/users/reset-password', { method: 'POST', body: { token, new_password } })
}

export function changePassword(token, { current_password, new_password }) {
  return request('/users/me/password', {
    method: 'PATCH',
    token,
    body: { current_password, new_password },
  })
}

export function uploadProfilePicture(userId, token, file) {
  const form = new FormData()
  form.append('file', file)
  return request(`/users/${userId}/picture`, { method: 'PATCH', token, body: form, isForm: true })
}

export function deleteProfilePicture(userId, token) {
  return request(`/users/${userId}/picture`, { method: 'DELETE', token })
}
