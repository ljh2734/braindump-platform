<template>
  <div class="profile-page">
    <div class="profile-container">
      <!-- 头像 & 用户名 -->
      <div class="profile-header">
        <img :src="user.avatar_url || DEFAULT_AVATAR" alt="头像" class="avatar" />
        <h1>{{ user.username }}</h1>
        <p class="user-id">ID: {{ user.id }}</p>

        <!-- 仅当不是自己时显示私信按钮 -->
        <button 
          v-if="currentUser && currentUser.id !== user.id"
          @click="goToChat(user.id)"
          class="profile-message-btn"
        >
          💬 发私信
        </button>

        <!-- 如果是自己，显示“查看私信” -->
        <button 
          v-else-if="currentUser && currentUser.id === user.id"
          @click="viewMessages"
          class="profile-message-btn"
        >
          📩 我的私信
        </button>
      </div>



      <!-- 统计信息 -->
      <div class="stats">
        <div class="stat-item">
          <div class="stat-value">{{ postCount }}</div>
          <div class="stat-label">帖子</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ likeCount }}</div>
          <div class="stat-label">获赞</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ questionCount }}</div>
          <div class="stat-label">？</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ commentCount }}</div>
          <div class="stat-label">评论</div>
        </div>

      </div>

      <!-- 帖子列表 -->
      <div class="posts-section">
        <h2>最近帖子</h2>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="posts.length === 0" class="no-posts">暂无帖子</div>
        <div v-else class="posts-grid">
          <PostCard
            v-for="post in posts"
            :key="post.id"
            :post="post"
            :current-user-id="currentUser?.id"
            @deleted="handlePostDeleted"
          />
        </div>
      </div>
    </div>
  </div>

    <!-- 悬浮按钮（固定右中） -->
  <div class="floating-buttons">
    <button @click="goHome" class="fab primary">🏠 </button>
    <button @click="refreshProfile" class="fab secondary">🔄 </button>
    <button @click="openEditUsername" class="fab secondary">✏️</button>
  <button @click="openAvatarUpload" class="fab secondary">🖼️</button>
  </div>


  <!-- 修改昵称弹窗 -->
  <div v-if="showUsernameModal" class="modal-overlay">
    <div class="modal">
      <h3>修改昵称</h3>
      <input v-model="newUsername" placeholder="请输入新昵称" class="modal-input" />
      <div class="modal-buttons">
        <button @click="showUsernameModal = false">取消</button>
        <button @click="updateUsername" class="primary">确定</button>
      </div>
    </div>
  </div>

  <!-- 上传头像弹窗 -->
  <div v-if="showAvatarModal" class="modal-overlay">
    <div class="modal">
      <h3>上传头像</h3>
      <input type="file" @change="e => avatarFile = e.target.files[0]" accept="image/*" />
      <div class="modal-buttons">
        <button @click="showAvatarModal = false">取消</button>
        <button @click="uploadAvatar" class="primary">上传</button>
      </div>
    </div>
  </div>

</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PostCard from '@/components/PostCard.vue'

const router = useRouter()
const user = ref({})
const posts = ref([])
const loading = ref(false)
const currentUser = ref(null) // 用于判断是否本人访问
const showUsernameModal = ref(false)
const newUsername = ref('')
const showAvatarModal = ref(false)
const avatarFile = ref(null)
const DEFAULT_AVATAR = '/static/default-avatar.png'
const postCount = ref(0)
const likeCount = ref(0)
const questionCount = ref(0)
const commentCount = ref(0)

// 获取当前登录用户（用于判断是否本人）
async function fetchCurrentUser() {
  const token = localStorage.getItem('token')
  if (!token) return null
  try {
    const res = await fetch('/api/user/me', {
      headers: { Authorization: 'Bearer ' + token }
    })
    if (res.ok) {
      const data = await res.json()
      currentUser.value = data
      return data
    }
  } catch (err) {
    console.error('获取当前用户失败:', err)
  }
  return null
}

// 获取目标用户信息
async function loadProfile() {
  loading.value = true
  try {
    const current = await fetchCurrentUser()
    if (!current) {
      router.push('/login')
      return
    }

    user.value = current

    // 获取我的帖子
    const token = localStorage.getItem('token')
    const res = await fetch('/api/posts/my-posts', {
      headers: { Authorization: 'Bearer ' + token }
    })
    const data = await res.json()
    if (data.success) {
      posts.value = data.data
      postCount.value = data.data.length
      likeCount.value = data.data.reduce((sum, p) => sum + (p.like_count || 0), 0)
      questionCount.value = data.data.reduce((sum, p) => sum + (p.question_count || 0), 0)
      commentCount.value = data.data.reduce((sum, p) => sum + (p.comment_count || 0), 0)
    }
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

function handlePostDeleted(deletedId) {
  posts.value = posts.value.filter(p => p.id !== deletedId)
}

function goHome() {
  router.push('/')
}

function refreshProfile() {
  loadProfile() // 重新加载个人资料和帖子
}

// 打开修改昵称
function openEditUsername() {
  newUsername.value = user.value.username
  showUsernameModal.value = true
}

// 打开头像上传
function openAvatarUpload() {
  avatarFile.value = null
  showAvatarModal.value = true
}

// 提交新昵称
async function updateUsername() {
  const token = localStorage.getItem('token')
  if (!newUsername.value.trim()) return alert('昵称不能为空')
  
  try {
    const res = await fetch('/api/user/username', {
      method: 'PUT',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username: newUsername.value.trim() })
    })
    
    if (res.ok) {
      const data = await res.json()
      user.value.username = data.username
      showUsernameModal.value = false
      alert('昵称修改成功')
    } else {
      const err = await res.json()
      alert(err.error || '修改失败')
    }
  } catch (err) {
    console.error(err)
    alert('网络错误')
  }
}

// 上传头像
async function uploadAvatar() {
  const file = avatarFile.value
  if (!file) return alert('请选择图片')
  
  const formData = new FormData()
  formData.append('avatar', file)
  
  const token = localStorage.getItem('token')
  try {
    const res = await fetch('/api/user/avatar', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token },
      body: formData
    })
    
    if (res.ok) {
      const data = await res.json()
      
      // 立即更新用户头像
      user.value.avatar_url = data.avatar_url
      
      showAvatarModal.value = false
      alert('头像上传成功')
    } else {
      const err = await res.json()
      alert(err.error || '上传失败')
    }
  } catch (err) {
    console.error(err)
    alert('上传失败')
  }
}

// 私信
function goToChat(userId) {
  router.push(`/messages/${userId}`)
}
function viewMessages() {
  router.push('/messages')
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background-color: #ffffff;
  padding: 24px 0;
  margin: 0 auto;
  min-width: 1000px;
  max-width: 1500px;
  width: 100%;
}

.profile-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 24px;
}

.profile-header {
  text-align: center;
  margin-bottom: 32px;
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  background: #eee;
  margin-bottom: 16px;
}

.profile-header h1 {
  font-size: 28px;
  color: #1f2937;
}

.email {
  color: #6b7280;
  margin-top: 4px;
}

.stats {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 40px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #4f46e5;
}

.stat-label {
  color: #6b7280;
  font-size: 14px;
}

.posts-section h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #1f2937;
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.loading, .no-posts {
  text-align: center;
  padding: 40px;
  color: #6b7280;
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
  font-size: 24px;
}

.fab.primary {
  background: #4f46e5;
  color: white;
}

.fab.secondary {
  background: white;
  color: #4f46e5;
}

@media (max-width: 768px) {
  .stats {
    flex-direction: column;
    gap: 16px;
  }
  .posts-grid {
    grid-template-columns: 1fr;
  }

    .floating-buttons {
    right: 16px;
  }
}

/* ========== 弹窗 ========== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 24px;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.modal h3 {
  margin: 0 0 16px;
  color: #1f2937;
}

.modal-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 16px;
}

.modal input[type="file"] {
  width: 100%;
  margin-bottom: 16px;
}

.modal-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-buttons button {
  padding: 6px 16px;
  border-radius: 6px;
  cursor: pointer;
}

.modal-buttons .primary {
  background: #4f46e5;
  color: white;
  border: none;
}

.profile-message-btn {
  margin-top: 12px;
  padding: 6px 16px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

</style>