// src/api/auth.js
import request from '@/utils/request'

export function register(email, password, username) {
  return request.post('/api/auth/register', { email, password, username })
}

// src/api/auth.js
export function login(email, password) {
  return request.post('/api/auth/login', { email, password })
}

//  获取当前用户（带 token）
export function getCurrentUser() {
  const token = localStorage.getItem('token')
  if (!token) {
    return Promise.reject(new Error('No token'))
  }
  return request.get('/api/user/me', {
    headers: { Authorization: `Bearer ${token}` }
  })
}

// 可选：登出
export function logout() {
  localStorage.removeItem('token')
}