<template>
  <div class="comment-item" :style="{ marginLeft: depth * 24 + 'px' }">
    <!-- 头像 & 用户名 -->
    <div class="comment-header">
      <img :src="userAvatar" alt="头像" class="avatar" />
       <span class="username">{{ currentUser?.username || '游客' }}</span>
      <div class="user-info">
        <span class="username">{{ comment.author.username }}</span>
        <span class="time">{{ formatDate(comment.created_at) }}</span>
      </div>
      <div class="comment-actions">
        <!-- 回复按钮 -->
        <button @click="handleReply" class="action-btn">↩️ 回复</button>

        <!-- 删除按钮（仅作者） -->
        <button
          v-if="canDelete"
          @click="handleDelete"
          class="action-btn delete-btn"
        >
          🗑️
        </button>
      </div>
    </div>

    <!-- 评论内容 -->
    <div class="comment-content" v-html="comment.content"></div>

    <!-- 互动区 -->
    <div class="interaction-bar">
      <button
        @click="toggleLike"
        :class="{ active: userInteractions.liked }"
        class="interact-btn"
      >
        👍 {{ comment.like_count }}
      </button>
      <button
        @click="toggleQuestion"
        :class="{ active: userInteractions.questioned }"
        class="interact-btn"
      >
        ❓ {{ comment.question_count }}
      </button>
    </div>

    <!-- 子评论 -->
    <div v-if="comment.replies && comment.replies.length" class="replies">
      <CommentItem
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :depth="depth + 1"
        @reply="emit('reply', $event)"
        @refresh="emit('refresh')"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
const DEFAULT_AVATAR = '/static/default-avatar.png'
const currentUser = ref(null)
const userAvatar = computed(() => {
  return currentUser.value?.avatar_url || DEFAULT_AVATAR
})

const props = defineProps({
  comment: {
    type: Object,
    required: true
  },
  depth: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['reply', 'refresh'])

// 获取当前用户 ID（从 token payload 解析）
const currentUserId = computed(() => {
  const token = localStorage.getItem('token')
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.user_id
  } catch (e) {
    return null
  }
})

// 是否可删除（自己）
const canDelete = computed(() => {

  const isAdmin = false
  return comment.value.author.id === currentUserId.value || isAdmin
})

const comment = ref(props.comment)
const userInteractions = ref({ liked: false, questioned: false })

// 格式化时间
function formatDate(dateStr) {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  if (diffHours < 1) return '刚刚'
  if (diffHours < 24) return `${diffHours}小时前`
  return date.toLocaleDateString('zh-CN')
}

// 加载互动状态
async function loadInteractions() {
  try {
    const res = await fetch(`/api/comments/${comment.value.id}/status`, {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
    })
    const data = await res.json()
    if (data.success) {
      userInteractions.value = data.data
    }
  } catch (e) {}
}

// 切换点赞
async function toggleLike() {
  const res = await fetch(`/api/comments/${comment.value.id}/like`, {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
  })
  const data = await res.json()
  if (data.success) {
    userInteractions.value.liked = data.data.liked
    comment.value.like_count = data.data.like_count
  }
}


async function toggleQuestion() {
  const res = await fetch(`/api/comments/${comment.value.id}/question`, {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
  })
  const data = await res.json()
  if (data.success) {
    userInteractions.value.questioned = data.data.questioned
    comment.value.question_count = data.data.question_count
  }
}

// 触发回复
function handleReply() {
  const replyText = `@${comment.value.author.username} `
  emit('reply', replyText)
}

// 删除评论
async function handleDelete() {
  if (!confirm('确定删除这条评论？')) return

  try {
    const res = await fetch(`/comments/${comment.value.id}`, {
      method: 'DELETE',
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
    })
    const data = await res.json()
    if (data.success) {
      alert('删除成功')
      emit('refresh') // 通知父组件重新加载评论
    } else {
      alert(data.message || '删除失败')
    }
  } catch (err) {
    alert('网络错误')
  }
}

onMounted(() => {
  loadInteractions()
})
</script>

<style scoped>
.comment-item {
  margin-top: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 12px;
  position: relative;
}

.comment-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  background: #eee;
}

.user-info {
  flex: 1;
}

.username {
  font-weight: 600;
  color: #1f2937;
}

.time {
  font-size: 12px;
  color: #9ca3af;
  margin-left: 8px;
}

.comment-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: none;
  border: none;
  font-size: 14px;
  cursor: pointer;
  color: #6b7280;
  padding: 2px 6px;
  border-radius: 4px;
}

.action-btn:hover {
  background: #e5e7eb;
}

.delete-btn {
  color: #ef4444;
}

.comment-content {
  line-height: 1.5;
  margin-bottom: 8px;
  word-break: break-word;
}

.interaction-bar {
  display: flex;
  gap: 12px;
}

.interact-btn {
  padding: 4px 10px;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
}

.interact-btn.active {
  background: #4f46e5;
  color: white;
  border-color: #4f46e5;
}

.replies {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e5e7eb;
}
</style>