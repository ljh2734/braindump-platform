// frontend/src/api/auth.js
const API_BASE = '/api'

export const register = (email, username, password) =>
  fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    credentials: 'include', // ← 关键：携带 Cookie
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password }),
  }).then((res) => res.json())

export const login = (email, password) =>
  fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  }).then((res) => res.json())

export const logout = () =>
  fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  }).then((res) => res.json())
