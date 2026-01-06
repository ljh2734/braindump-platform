<template>
  <div class="messages-container">
    <div class="contacts-sidebar">
      <h3 class="sidebar-title">私信</h3>
      <div 
        v-for="contact in contacts" 
        :key="contact.user.id" 
        class="contact-item"
        :class="{ active: contact.user.id === selectedUserId }"
        @click="selectContact(contact.user.id)"
      >
        <!-- 头像区域 -->
        <div class="avatar-wrapper">
          <img 
            :src="contact.user.avatar_url || DEFAULT_AVATAR" 
            class="contact-avatar" 
          />
        </div>

        <!-- 信息区域 -->
        <div class="contact-info">
          <div class="contact-header">
            <div class="contact-name">{{ contact.user.username }}</div>
          </div>
          <div class="last-message-preview">
            {{ contact.last_message?.content || '点击开始聊天' }}
          </div>
        </div>

        <div class="contact-actions" v-if="contact.user.id !== currentUserId">
        <button 
          @click.stop="toggleBlock(contact.user.id)"
          class="block-btn"
        >
          {{ isBlocked(contact.user.id) ? '解除拉黑' : '拉黑' }}
        </button>
      </div>

      </div>
    </div>
    
    <div class="chat-placeholder" v-if="!selectedUserId">
      选择一个联系人开始聊天
    </div>
  </div>

    <!-- 悬浮按钮 -->
  <div class="floating-buttons">
    <button @click="goHome" class="fab primary">🏠</button>
    <button @click="refreshContacts" class="fab secondary">🔄</button>
  </div>

</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const contacts = ref([])
const selectedUserId = ref(null)
const DEFAULT_AVATAR = '/static/default-avatar.png'
const currentUserId = ref(null)
const blockedUsers = ref(new Set()) // 存储被当前用户拉黑的用户

async function loadContacts() {
  const token = localStorage.getItem('token')
  const res = await fetch('/api/messages/contacts', {
    headers: { Authorization: `Bearer ${token}` }
  })
  const data = await res.json()
  contacts.value = data.contacts || []
}

function selectContact(userId) {
  router.push(`/messages/${userId}`)
}

onMounted(() => {
  currentUserId.value = parseCurrentUserId()
  loadBlockedUsers() 
  loadContacts()
})

function goHome() {
  router.push('/')
}

function refreshContacts() {
  loadContacts() // 重新加载联系人
}

// 解析当前用户ID
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

// 加载当前用户的拉黑列表
async function loadBlockedUsers() {
  const token = localStorage.getItem('token')
  if (!token) return
  try {
    const res = await fetch('/api/block/list', {
      headers: { Authorization: `Bearer ${token}` }
    })
    const data = await res.json()
    blockedUsers.value = new Set(data.blocked_user_ids || [])
  } catch (error) {
    console.error('加载拉黑列表失败:', error)
  }
}

// 判断是否拉黑某用户
function isBlocked(userId) {
  return blockedUsers.value.has(userId)
}

// 拉黑/解除拉黑
async function toggleBlock(userId) {
  if (userId === currentUserId.value) return
  const token = localStorage.getItem('token')
  try {
    const res = await fetch('/api/block/toggle', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: userId })
    })
    const data = await res.json()
    if (data.blocked) {
      blockedUsers.value.add(userId)
    } else {
      blockedUsers.value.delete(userId)
    }
  } catch (err) {
    alert('操作失败，请重试')
    console.error('拉黑操作失败:', err)
  }
}
</script>

<style scoped>
.messages-container {
  display: flex;
  height: calc(100vh - 60px);
  background-color: #ffffff; /* 浅灰背景 */
}

/* 左侧边栏 */
.contacts-sidebar {
  width: 320px;
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
  background: white;
  display: flex;
  flex-direction: column;
}

.sidebar-title {
  padding: 16px 20px;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  border-bottom: 1px solid #f3f4f6;
}

/* 联系人项 */
.contact-item {
  display: flex;
  padding: 14px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  gap: 14px;
}

.contact-item:hover {
  background-color: #f9fafb;
}

.contact-item.active {
  background-color: #eff6ff;
  border-left: 3px solid #3b82f6;
}

/* 头像 */
.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.contact-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
}

/* 在线状态指示器 */
.online-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  background: #10b981;
  border: 2px solid white;
  border-radius: 50%;
}

/* 联系人信息 */
.contact-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.contact-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.contact-name {
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 最后消息时间 */
.last-message-time {
  font-size: 12px;
  color: #9ca3af;
  flex-shrink: 0;
}

/* 消息预览 */
.last-message-preview {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 占位提示 */
.chat-placeholder {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #9ca3af;
  font-size: 18px;
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
  font-size: 24px; /* 调整图标大小 */
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

/* 拉黑按钮样式 */
.contact-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.block-btn {
  padding: 4px 8px;
  font-size: 12px;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.block-btn:hover {
  background: #fecaca;
}

</style>