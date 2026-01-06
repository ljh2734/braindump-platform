<template>
  <div class="my-posts-container">
    <div class="header">
      <h1>我的帖子</h1>
    </div>

    <div v-if="loading" class="loading-state">
      <p>加载中...</p>
    </div>
    <div v-else-if="posts.length === 0" class="empty-state">
      <p>你还没有发布任何帖子</p>
      <button @click="openCreatePost" class="create-btn">立即发帖</button>
    </div>
    <div v-else class="posts-grid">
      <PostCard v-for="post in posts" :key="post.id" :post="post" :current-user-id="currentUserId"  @deleted="handlePostDeleted"/>
    </div>

    <!-- ========== 悬浮按钮 ========== -->
    <div class="floating-buttons">
      <button @click="goHome" class="fab home">🏠</button>
      <button @click="openCreatePost" class="fab primary">📝</button>
      <button @click="refreshPosts" class="fab secondary">🔄</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PostCard from '@/components/PostCard.vue'

const router = useRouter()
const posts = ref([])
const loading = ref(false)
const currentUserId = ref(null) 

async function loadMyPosts() {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/posts/my-posts', {
      headers: { Authorization: 'Bearer ' + token }
    })
    const data = await res.json()
    if (data.success) {
      posts.value = data.data
    }
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function fetchCurrentUserId() {
  const token = localStorage.getItem('token')
  if (!token) return null

  try {
    const res = await fetch('/api/user/me', {
      headers: { Authorization: 'Bearer ' + token }
    })
    if (res.ok) {
      const userData = await res.json()
      return userData.id
    }
  } catch (err) {
    console.error('获取用户信息失败:', err)
  }
  return null
}

// ===== 处理帖子删除事件 =====
function handlePostDeleted(deletedId) {
  posts.value = posts.value.filter(p => p.id !== deletedId)
}

// ===== 悬浮按钮功能 =====
function goHome() {
  router.push('/')
}
function openCreatePost() {
  router.push('/post/create')
}
function refreshPosts() {
  loadMyPosts()
}

// 初始加载
onMounted(async () => {
  currentUserId.value = await fetchCurrentUserId()
  loadMyPosts()
})

</script>

<style scoped>
.my-posts-container {
  max-width: 1200px;
  margin: 48px auto;
  padding: 0 24px;
  min-height: 100vh;
  position: relative;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column; 
  align-items: center; 
}

.header {
  text-align: center;
  margin-bottom: 32px;
  width: 100%; /* 防止因 flex 缩小 */
  max-width: 600px;
}

h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: -0.5px;
  text-align: center;
}

/* ========== 帖子网格：每行3个 ========== */
.posts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr); /* 每行n个 */
  gap: 20px;
  width: 100%;
  min-width: 1000px;
}

/* ========== 空状态 & 加载状态 ========== */
.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
  font-size: 18px;
}

.empty-state .create-btn {
  margin-top: 20px;
  padding: 10px 24px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.empty-state .create-btn:hover {
  background: #4338ca;
}

/* ========== 悬浮按钮 ========== */
.floating-buttons {
  position: fixed;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 16px;
  z-index: 99;
}

.fab {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  font-weight: bold;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  font-size: 20px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.fab:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.22);
}

.fab.primary {
  background: #4f46e5;
  color: rgb(255, 255, 255);
}

.fab.secondary,
.fab.home {
  background: white;
  color: #4f46e5;
  border: 2px solid #e0e0ff;
}

/* ========== 响应式：小屏单列 ========== */
@media (max-width: 768px) {
  .my-posts-container {
    margin: 16px auto;
    padding: 0 16px;
  }

  h1 {
    font-size: 24px;
    margin-bottom: 24px;
  }

  .posts-grid {
    grid-template-columns: 1fr; /* 移动端单列 */
    gap: 20px;
  }

  .floating-buttons {
    right: 16px;
    gap: 12px;
  }

  .fab {
    width: 56px;
    height: 56px;
    font-size: 18px;
  }
}
</style>