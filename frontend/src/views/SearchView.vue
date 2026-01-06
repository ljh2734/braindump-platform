<template>
  <div class="search-container">
    <!-- 搜索结果标题 -->
    <div class="search-header">
      <h2>🔍 搜索结果：{{ query || '（无关键词）' }}</h2>
      <p v-if="!loading && posts.length > 0" class="result-count">
        共找到 {{ posts.length }} 个帖子
      </p>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在搜索...</p>
    </div>

    <!-- 空结果 -->
    <div v-else-if="posts.length === 0" class="empty-state">
      <div class="empty-icon">🔍</div>
      <h3>未找到相关帖子</h3>
      <p>试试其他关键词，如“Vue”、“学习”或“问题”</p>
    </div>

    <!-- 帖子列表 -->
    <div v-else class="posts-grid">
      <PostCard v-for="post in posts" :key="post.id" :post="post" />
    </div>
  </div>
  <!-- 悬浮按钮 -->
  <div class="floating-buttons">
    <button @click="goHome" class="fab secondary">🏠</button>
    <button @click="goToCreate" class="fab primary">📝</button>
    <button @click="refreshSearch" class="fab secondary">🔄</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PostCard from '@/components/PostCard.vue'
import { useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const query = route.query.q || ''
const posts = ref([])
const loading = ref(false)

// 搜索逻辑
async function handleSearch(q) {
  if (!q) return
  loading.value = true
  try {
    const res = await fetch(`/api/posts/search?q=${encodeURIComponent(q)}`)
    const data = await res.json()
    posts.value = data.success ? data.data.posts || [] : []
  } finally {
    loading.value = false
  }
}

//调用 handleSearch
onMounted(() => {
  handleSearch(route.query.q || '')
})

function goHome() {
  router.push('/')
}

function goToCreate() {
  router.push('/post/create')
}

function refreshSearch() {
  // 重新执行搜索
  handleSearch(route.query.q || '')
}

</script>

<style scoped>
.search-container {
  min-height: 100vh;
  background-color: #ffffff;
  padding: 32px 0;
}

/* 搜索标题区域 */
.search-header {
  text-align: center;
  margin-bottom: 32px;
}

.search-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px;
}

.result-count {
  color: #6b7280;
  font-size: 16px;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6b7280;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #4f46e5;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-state h3 {
  font-size: 22px;
  color: #1f2937;
  margin: 0 0 8px;
}

.empty-state p {
  max-width: 400px;
  margin: 0 auto;
  line-height: 1.6;
}

/* ========== 帖子网格（关键） ========== */
.posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
}

/* 确保 PostCard 不被拉伸 */
.posts-grid .post-card {
  height: auto;
  max-width: 100%;
}

/* ========== 悬浮按钮 ========== */
.floating-buttons {
  position: fixed;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 99;
}

.fab {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  font-size: 24px; /* 调整这个值来改变图标的大小 */
  transition: transform 0.2s;
}

.fab.primary {
  background: #4f46e5;
  color: white;
}

.fab.secondary {
  background: white;
  color: #4f46e5;
}
</style>