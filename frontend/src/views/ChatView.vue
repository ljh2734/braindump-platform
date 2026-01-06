<template>
  <div class="chat-container">
    <!-- 加载中提示 -->
    <div v-if="!targetUser" class="loading">加载中...</div>

    <!-- 顶部信息栏 -->
    <div v-else class="chat-header">
        <img 
          :src="getAvatarApiUrl(targetUser?.avatar_url)" 
          alt="头像" 
          class="avatar" 
        />
      <div class="user-info">
        <h3>{{ targetUser.username }}</h3>
        <p v-if="isOnline">在线</p>
        <p v-else>离线</p>
      </div>
    </div>

    <!-- 聊天消息区 -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="msg in messages" :key="msg.id" class="message-row">
        <!-- 对方消息（左侧 + 头像） -->
        <div v-if="msg.sender_id !== currentUserId" class="message-left">
          <img :src="getAvatarApiUrl(targetUser?.avatar_url)" alt="对方头像" class="peer-avatar" />
          <div class="message-bubble left">
            <span>{{ msg.content }}</span> 
          </div>
          <div class="message-time">{{ formatTime(msg.created_at) }}</div>
        </div>

        <!-- 自己消息（右侧） -->
        <div v-else class="message-right">
          <div class="message-bubble right">
            <span>{{ msg.content }}</span> 
          </div>
          <div class="message-time">{{ formatTime(msg.created_at) }}</div>
        </div>
      </div>

      <!-- 悬浮按钮（固定右中） -->
      <div class="floating-buttons">
        <button @click="goHome" class="fab primary">🏠</button>
        <button @click="refreshChat" class="fab secondary">🔄</button>
        <button @click="goToMessages" class="fab secondary">🧍‍♂️</button>
      </div>

    </div>

    <!-- 输入区 -->
    <div class="chat-input">
      <textarea
        v-model="newMessage"
        placeholder="输入消息..."
        @keydown.enter.exact.prevent="sendMessage"
        @keydown.ctrl.enter.prevent="newMessage += '\n'"
        class="input-textarea"
      ></textarea>
      <button @click="sendMessage" class="send-btn">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
const DEFAULT_AVATAR = '/static/default-avatar.png'
const route = useRoute()
const targetUserId = parseInt(route.params.userId)
const router = useRouter()
// 当前用户 ID（从 token 解析）
const currentUserId = ref(null)

// 目标用户信息
const targetUser = ref(null)
const messages = ref([])
const newMessage = ref('')
const isOnline = ref(false)

// 解析当前用户 ID
function parseCurrentUserId() {
  const token = localStorage.getItem('token')
  if (!token) return null
  try {
    const payloadBase64 = token.split('.')[1]
    const payloadJson = atob(payloadBase64.replace(/-/g, '+').replace(/_/g, '/'))
    const payload = JSON.parse(payloadJson)
    return parseInt(payload.sub)
  } catch (e) {
    console.error('解析 token 失败', e)
    return null
  }
}

function goHome() {
  router.push('/')
}

function goToMessages() {
  router.push('/messages')
}

function refreshChat() {
  // 重新加载目标用户和消息
  loadTargetUser()
  loadMessages()
}

// 时间格式化
function formatTime(dateStr) {
  const msgDate = new Date(dateStr)
  const now = new Date()
  
  // 判断是否是今天
  const isSameDay = (d1, d2) => 
    d1.getDate() === d2.getDate() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getFullYear() === d2.getFullYear()

  if (isSameDay(msgDate, now)) {
    // 今天：显示时分
    return msgDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  
  // 判断是否是昨天
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (isSameDay(msgDate, yesterday)) {
    return '昨天'
  }

  // 更早：显示 年-月-日
  const year = msgDate.getFullYear()
  const month = String(msgDate.getMonth() + 1).padStart(2, '0')
  const day = String(msgDate.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 加载目标用户
async function loadTargetUser() {
  try {
    const res = await fetch(`/api/user/${targetUserId}`)
    if (!res.ok) throw new Error('用户不存在')
    targetUser.value = await res.json()
  } catch (error) {
    console.error('加载用户失败:', error)
  }
}

// 加载头像
function getAvatarApiUrl(avatarUrl) {
  if (!avatarUrl) return '/static/default-avatar.png'
  
  // 如果是 /static/uploads/avatars/... 格式，转换为 API 路径
  if (avatarUrl.startsWith('/static/uploads/avatars/')) {
    const filename = avatarUrl.split('/').pop()
    return `/api/user/avatar/${filename}`
  }
  
  // 如果已经是 API 路径或外部 URL，直接返回
  return avatarUrl
}

// 加载消息
async function loadMessages() {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/messages/${targetUserId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!res.ok) throw new Error('获取消息失败')
    const data = await res.json()
    messages.value = data.messages || []
  } catch (error) {
    console.error('加载消息失败:', error)
  }
}

// 发送消息
async function sendMessage() {
  if (!targetUser.value) {
    alert('用户信息未加载')
    return
  }

  if (!newMessage.value.trim()) return

  const token = localStorage.getItem('token')
  if (!token) {
    alert('请先登录')
    return
  }

  const messageData = {
    content: newMessage.value,
    receiver_id: targetUserId
  }

  try {
    const res = await fetch('/api/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(messageData)
    })

    if (res.ok) {
      const savedMsg = await res.json()
      messages.value.push(savedMsg)
      newMessage.value = ''
    } else {
      const errorData = await res.json().catch(() => ({}))
      alert(`发送失败: ${errorData.error || '未知错误'}`)
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    alert('网络错误，请重试')
  }
}

// 初始化
onMounted(async () => {
  currentUserId.value = parseCurrentUserId()
  await loadTargetUser()
    // ====== 检查拉黑状态 ======
  if (targetUser.value) {
    const token = localStorage.getItem('token')
    try {
      const res = await fetch(`/api/block/check/${targetUserId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      if (data.blocked_by_me) {
        alert('你已拉黑该用户，无法发送消息')
        router.push('/messages')
        return
      }
      if (data.blocked_me) {
        alert('对方已拉黑你，无法发送消息')
        router.push('/messages')
        return
      }
    } catch (error) {
      console.error('检查拉黑状态失败:', error)
    }
  }
  await loadMessages()
})
</script>

<style scoped>
.chat-container {
  height: 100vh;
  width: 50vw;
  max-width: none;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background-color: #7fc5cd;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 顶部信息栏 */
.chat-header {
  padding: 1rem;
  background: rgb(175, 241, 253);
  border-bottom: 1px solid #e3f3f4;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}

.user-info h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #333;
}

.user-info p {
  margin: 0;
  font-size: 0.8rem;
  color: #666;
}

/* 消息区 */
.chat-messages {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  width: 100%;
}

.message-row {
  display: flex;
  width: 100%;
}


.message-left {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.6rem;
  max-width: 70%;
}
.peer-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.message-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end; 
  margin-left: auto;
  max-width: 70%;
}

.message-bubble {
  padding: 0.75rem 1rem;
  border-radius: 18px;
  line-height: 1.4;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: anywhere;
  white-space: normal;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  max-width: 100%; /* 改为 100%，让父容器控制宽度 */
}

.message-content {
  margin-bottom: 4px; 
}

.message-time {
  font-size: 0.7rem;
  color: #ffffff;
  opacity: 0.8;
  margin-top: 4px;
  text-align: right;
  width: 100%;
  padding-right: 1rem; /* 与气泡右边缘对齐 */
}

.message-bubble.left {
  background-color: #e0e0e0;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-bubble.right {
  background-color: #007bff;
  color: white;
  border-bottom-right-radius: 4px;
}

/* 输入区 */
.chat-input {
  padding: 1rem;
  background: white;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 0.5rem;
}

.input-textarea {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 20px;
  resize: none;
  min-height: 50px;
  max-height: 120px;
  font-size: 1rem;
  outline: none;
}

.input-textarea:focus {
  border-color: #007bff;
}

.send-btn {
  padding: 0.75rem 1.5rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background 0.2s;
}

.send-btn:hover {
  background-color: #0056b3;
}

/* 加载提示 */
.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  font-size: 1.2rem;
  color: #666;
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
  .floating-buttons {
    right: 16px;
  }
}

</style>