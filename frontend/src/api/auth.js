// ============================================================
//  认证 API
// ============================================================
import request from './request'

export function login(username, password) {
  return request.post('/auth/login', { username, password })
}

export function getMe() {
  return request.get('/auth/me')
}

export function refreshToken(refreshToken) {
  return request.post('/auth/refresh', { refresh_token: refreshToken })
}

export function changePassword(oldPassword, newPassword) {
  return request.put('/auth/password', { old_password: oldPassword, new_password: newPassword })
}
