// src/api/post.js
import request from '@/utils/request'

export function getPosts(page = 1) {
  const token = localStorage.getItem('token')
  return request.get('/api/posts', {
    params: { page },
    headers: { Authorization: `Bearer ${token}` }
  })
}


/*export function getHotTags() {
  const token = localStorage.getItem('token')
  return request.get('/api/tags/hot', {
    headers: { Authorization: `Bearer ${token}` }
  })
}*/