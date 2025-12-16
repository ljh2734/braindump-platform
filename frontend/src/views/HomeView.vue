<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <header class="navbar">
      <div class="logo" @click="goHome">🧠 Braindump</div>
      <!-- 导航按钮组 -->
      <div class="nav-buttons">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="{ active: currentTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>
      <!-- 搜索框 -->
      <div class="search-box">
        <input
          v-model="searchQuery"
          @keyup.enter="handleSearch"
          placeholder="搜索帖子..."
          class="search-input"
        />
        <button @click="handleSearch" class="search-btn">🔍</button>
      </div>
      <!-- 用户头像（固定右上角） -->
      <div class="user-info" @click="toggleProfileMenu">
        <img :src="currentUser?.avatar || '/default-avatar.png'" alt="头像" class="avatar" />
        <span class="username">{{ currentUser?.username || '游客' }}</span>
        <!-- 下拉菜单 -->
        <div v-if="showProfileMenu" class="profile-menu">
          <div @click="goProfile">个人主页</div>
          <div @click="goMyPosts">我的帖子</div>
          <div @click="logout">退出登录</div>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <div class="posts-grid" ref="postsContainer">
        <div v-if="loading && posts.length === 0" class="loading">加载中...</div>
        <div v-else-if="posts.length === 0" class="no-posts">暂无帖子</div>
        <PostCard v-for="post in posts" :key="post.id" :post="post" class="post-card" />
      </div>
    </main>

    <!-- 右侧悬浮按钮 -->
    <div class="floating-buttons">
      <button @click="openCreatePost" class="fab primary">📝 发帖</button>
      <button @click="refreshPosts" class="fab secondary">🔄 刷新</button>
      
      <!-- 🔥 新增：仅在“？”页面显示的周期切换按钮（垂直排列在刷新按钮下方） -->
      <div v-if="currentTab === 'questions_7d'" class="period-toggle">
        <button
          class="period-btn"
          :class="{ active: questionPeriod === '7d' }"
          @click="setQuestionPeriod('7d')"
        >
          本周
        </button>
        <button
          class="period-btn"
          :class="{ active: questionPeriod === '30d' }"
          @click="setQuestionPeriod('30d')"
        >
          本月
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import PostCard from '@/components/PostCard.vue'
import { getCurrentUser, logout as apiLogout } from '@/api/auth'

const router = useRouter()

// === 响应式数据 ===
const posts = ref([])
const loading = ref(false)
const hasMore = ref(true)
const currentTab = ref('newest')
const searchQuery = ref('')
const currentUser = ref(null)
const showProfileMenu = ref(false)

// 🔥 新增：问号周期状态（默认7天）
const questionPeriod = ref('7d')

// === 导航标签 ===
// 将 ? 的 key 改为 questions_7d，以便默认使用7天数据
const tabs = [
  { key: 'recommended', label: '推荐' },
  { key: 'roam', label: '漫游' },
  { key: 'questions_7d', label: '?' }, // ← 关键：使用后端支持的 sort key
  { key: 'newest', label: '最新' }
]

// === 🔥 辅助函数：获取当前实际 sort 参数 ===
function getCurrentSort() {
  if (currentTab.value === 'questions_7d') {
    return questionPeriod.value === '7d' ? 'questions_7d' : 'questions_30d'
  }
  return currentTab.value
}

// === 加载帖子（游标分页）===
async function loadPosts(isRefresh = false) {
  if (loading.value || (!hasMore.value && !isRefresh)) return
  loading.value = true
  if (isRefresh) {
    posts.value = []
    hasMore.value = true
  }

  try {
    let url
    const params = new URLSearchParams()
    const sortParam = getCurrentSort() // ← 使用动态 sort

    if (sortParam === 'roam') {
      url = '/api/posts/roam'
    } else {
      params.append('sort', sortParam)
      params.append('limit', '10')
      if (!isRefresh && posts.value.length > 0) {
        const lastPost = posts.value[posts.value.length - 1]
        params.append('after', lastPost.created_at)
      }
      url = `/api/posts?${params.toString()}`
    }

    const response = await fetch(url)
    const data = await response.json()
    if (data.success) {
      let newPosts = []
      if (sortParam === 'roam') {
        newPosts = data.data.posts || []
        hasMore.value = true
      } else {
        newPosts = data.data.posts || []
        hasMore.value = data.data.has_more !== undefined ? data.data.has_more : newPosts.length >= 10
      }
      if (isRefresh) {
        posts.value = newPosts
      } else {
        posts.value.push(...newPosts)
      }
    }
  } catch (err) {
    console.error('加载失败:', err)
    if (posts.value.length === 0) alert('加载失败，请刷新页面')
  } finally {
    loading.value = false
  }
}

// === 事件处理 ===
function switchTab(tabKey) {
  currentTab.value = tabKey
  // 切出 ? 页面时重置周期（可选）
  if (tabKey !== 'questions_7d') {
    questionPeriod.value = '7d'
  }
  loadPosts(true)
}

// 🔥 新增：设置周期并刷新
function setQuestionPeriod(period) {
  questionPeriod.value = period
  loadPosts(true)
}

function handleSearch() {
  if (searchQuery.value.trim()) {
    router.push(`/search?q=${encodeURIComponent(searchQuery.value.trim())}`)
  }
}

function refreshPosts() {
  loadPosts(true)
}

function openCreatePost() {
  router.push('/post/create')
}

function toggleProfileMenu() {
  showProfileMenu.value = !showProfileMenu.value
}

// === 路由跳转 ===
function goHome() { router.push('/') }
function goProfile() { router.push('/profile') }
function goMyPosts() { router.push('/my-posts') }

// === 用户登出 ===
async function logout() {
  try {
    await apiLogout()
    localStorage.removeItem('token')
    router.push('/login')
  } catch (err) {
    console.error('登出失败', err)
  }
}

// === 滚动监听（瀑布流）===
function handleScroll() {
  if (loading.value || !hasMore.value) return
  const { scrollTop, scrollHeight, clientHeight } = document.documentElement
  if (scrollTop + clientHeight >= scrollHeight - 200) {
    loadPosts(false)
  }
}

// === 初始化 ===
onMounted(() => {
  getCurrentUser().then(res => {
    currentUser.value = res.data
  }).catch(() => {})
  loadPosts(true)
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
/* ========== 保持原有样式完全不变 ========== */
.home-container {
  min-height: 100vh;
  background-color: #f9fafb;
  position: relative;
}

.navbar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  gap: 20px;
}

.logo {
  font-size: 24px;
  font-weight: bold;
  color: #4f46e5;
  cursor: pointer;
  min-width: 120px;
}

.nav-buttons {
  display: flex;
  gap: 12px;
}

.nav-buttons button {
  padding: 6px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 20px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-buttons button.active,
.nav-buttons button:hover {
  background: #4f46e5;
  color: white;
  border-color: #4f46e5;
}

.search-box {
  flex: 1;
  display: flex;
  max-width: 400px;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 20px 0 0 20px;
  outline: none;
}

.search-btn {
  padding: 8px 16px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 0 20px 20px 0;
  cursor: pointer;
}

.user-info {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  min-width: 120px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  background: #eee;
}

.username {
  font-size: 14px;
  color: #333;
}

.profile-menu {
  position: absolute;
  top: 45px;
  right: 0;
  background: white;
  border: 1px solid #eee;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  z-index: 101;
  width: 120px;
}

.profile-menu > div {
  padding: 8px 12px;
  cursor: pointer;
}

.profile-menu > div:hover {
  background: #f5f5f5;
}

.main-content {
  padding: 24px;
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); /* 👈 保持一行4个 */
  gap: 24px;
  max-width: 1400px; /* 👈 保持宽屏 */
  margin: 0 auto;
}

.loading,
.no-posts {
  text-align: center;
  padding: 40px;
  color: #6b7280;
  grid-column: 1 / -1;
}

/* ========== 悬浮按钮（关键：保持原位置） ========== */
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
}

.fab.primary {
  background: #4f46e5;
  color: white;
}

.fab.secondary {
  background: white;
  color: #4f46e5;
}

/* 🔥 新增：周期切换按钮样式（紧贴刷新按钮下方） */
.period-toggle {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.period-btn {
  width: 60px;
  height: 32px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 16px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.period-btn.active,
.period-btn:hover {
  background: #4f46e5;
  color: white;
  border-color: #4f46e5;
}

/* 响应式 */
@media (max-width: 768px) {
  .navbar {
    flex-wrap: wrap;
    gap: 12px;
  }
  .nav-buttons,
  .search-box,
  .user-info {
    order: 2;
    width: 100%;
  }
  .search-box {
    max-width: none;
  }
  .posts-grid {
    grid-template-columns: 1fr;
    padding: 0 12px;
  }
  .floating-buttons {
    right: 16px;
  }
  /* 小屏下周期按钮横向排列 */
  .period-toggle {
    flex-direction: row;
    gap: 6px;
  }
  .period-btn {
    width: 50px;
    height: 28px;
  }
}
</style>