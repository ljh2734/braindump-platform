// src/api/interaction.js
import request from '@/utils/request'

export function toggleLike(targetType, targetId) {
  const token = localStorage.getItem('token')
  return request.post(`/api/interactions/${targetType}s/${targetId}/like`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function toggleQuestion(targetType, targetId) {
  const token = localStorage.getItem('token')
  return request.post(`/api/interactions/${targetType}s/${targetId}/question`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function getInteractionStatus(targetType, targetId) {
  const token = localStorage.getItem('token')
  return request.get(`/api/interactions/${targetType}s/${targetId}/status`, {
    headers: { Authorization: `Bearer ${token}` }
  })
}