<template>
  <div class="profile-container">
    <div class="profile-card">
      <div class="avatar-section">
        <img :src="user.avatar_url || '/default-avatar.png'" class="big-avatar" />
        <label class="upload-btn">
          更换头像
          <input type="file" accept="image/*" @change="uploadAvatar" hidden />
        </label>
      </div>
      <div class="info-section">
        <h2>{{ user.username }}</h2>
        <p>注册时间：{{ formatDate(user.created_at) }}</p>
        <p>邮箱：{{ user.email }}</p>
      </div>
    </div>

    <div class="actions">
      <button @click="router.push('/my-posts')">我的帖子</button>
      <button @click="logout">退出登录</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCurrentUser, logout as apiLogout } from '@/api/auth'

const router = useRouter()
const user = ref(null)

async function loadUser() {
  const res = await getCurrentUser()
  user.value = res.data
}

async function uploadAvatar(e) {
  const file = e.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('avatar', file)

  try {
    const res = await fetch('/api/user/avatar', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
      body: formData
    })
    const data = await res.json()
    if (data.success) {
      user.value.avatar_url = data.data.avatar_url
      alert('头像更新成功！')
    }
  } catch (err) {
    alert('上传失败')
  }
}

async function logout() {
  await apiLogout()
  localStorage.removeItem('token')
  router.push('/login')
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadUser()
})
</script>

<style scoped>
.profile-container {
  max-width: 600px;
  margin: 40px auto;
  padding: 0 16px;
}

.profile-card {
  background: white;
  border-radius: 16px;
  padding: 32px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.big-avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 20px;
  background: #eee;
}

.upload-btn {
  display: inline-block;
  padding: 8px 16px;
  background: #4f46e5;
  color: white;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
}

.info-section h2 {
  margin: 16px 0;
  font-size: 24px;
}

.actions {
  margin-top: 32px;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: #f3f4f6;
  cursor: pointer;
}
</style>