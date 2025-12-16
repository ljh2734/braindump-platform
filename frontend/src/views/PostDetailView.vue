<template>
  <div class="post-detail-container">
    <!-- 右侧悬浮按钮 -->
    <div class="floating-buttons">
      <button @click="goHome" class="fab home">🏠</button>
      <button @click="openCreatePost" class="fab primary">📝</button>
      <button @click="refresh" class="fab secondary">🔄</button>
      <button v-if="!inReplyMode" @click="openCommentBox" class="fab comment">💬</button>
    </div>

    <main class="main-content">
      <!-- 帖子内容区 -->
      <div v-if="post" class="post-card">
        <div class="author-info">
          <img :src="post.author.avatar || '/default-avatar.png'" alt="头像" class="avatar" />
          <div class="author-meta">
            <div class="nickname">{{ post.author.nickname }}</div>
            <div class="user-id">@{{ post.author.id }}</div>
          </div>
        </div>

        <h1 class="post-title">{{ post.title }}</h1>
        <div class="post-time">{{ formatTime(post.created_at) }}</div>
        <div class="post-body" v-html="post.content"></div>

        <div class="interaction-buttons">
          <button class="like-btn">👍 {{ post.like_count || 0 }}</button>
          <button class="question-btn">❓ {{ post.question_count || 0 }}</button>
        </div>
      </div>
      <div v-else class="loading-post">加载中...</div>

      <!-- 评论区标题 & 排序（仅主评论） -->
      <div v-if="!inReplyMode" class="comments-header">
        <h2>评论 ({{ totalComments }})</h2>
        <div class="sort-toggle">
          <button :class="{ active: commentSort === 'hot' }" @click="setCommentSort('hot')">最热</button>
          <button :class="{ active: commentSort === 'time_desc' }" @click="setCommentSort('time_desc')">最新</button>
        </div>
      </div>

      <!-- 子评论区标题 -->
      <div v-else class="reply-header">
        <div class="back-to-post" @click="exitReplyMode">← 返回帖子</div>
        <div class="reply-target">
          回复：
          <strong>{{ replyTarget?.author?.nickname }}</strong>
          <p>{{ replyTarget?.content }}</p>
        </div>
      </div>

      <!-- 评论列表 -->
      <div class="comments-list" ref="commentsContainer">
        <div v-for="comment in comments" :key="comment.id" class="comment-item">
          <img :src="comment.author.avatar || '/default-avatar.png'" alt="头像" class="comment-avatar" />
          <div class="comment-content">
            <div class="comment-author">{{ comment.author.nickname }}</div>
            <div class="comment-time">{{ formatTime(comment.created_at) }}</div>
            <div class="comment-text">{{ comment.content }}</div>

            <!-- 主评论才显示子回复预览 -->
            <div
              v-if="!inReplyMode && comment.sub_count > 0"
              class="sub-reply-preview"
              @click="enterReplyMode(comment)"
            >
              <div class="hot-sub">{{ comment.hot_reply?.content || '查看回复' }}</div>
              <div class="sub-count" v-if="comment.sub_count > 1">还有 {{ comment.sub_count - 1 }} 条回复</div>
            </div>
          </div>
          <div class="comment-actions">
            <button class="like-btn small">👍 {{ comment.like_count || 0 }}</button>
            <button class="question-btn small">❓ {{ comment.question_count || 0 }}</button>
            <button v-if="inReplyMode" class="reply-btn" @click="openReplyBox(comment)">💬</button>
          </div>
        </div>

        <div v-if="loadingComments && comments.length === 0" class="loading">加载评论中...</div>
        <div v-else-if="comments.length === 0" class="no-comments">
          {{ inReplyMode ? '暂无回复' : '暂无评论' }}
        </div>
      </div>
    </main>

    <!-- 底部评论框 -->
    <div v-if="showCommentBox" class="comment-box-overlay">
      <div class="comment-box">
        <div class="comment-box-header">
          <span>{{ inReplyMode ? `回复 ${replyTo?.nickname}` : '发表评论' }}</span>
          <button @click="closeCommentBox" class="close-btn">×</button>
        </div>
        <textarea
          v-model="commentContent"
          placeholder="写下你的想法..."
          class="comment-input"
          :disabled="posting"
        ></textarea>
        <div class="comment-box-footer">
          <button @click="closeCommentBox" :disabled="posting">取消</button>
          <button @click="submitComment" :disabled="!commentContent.trim() || posting" class="publish-btn">
            {{ posting ? '发送中...' : '发布' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const route = useRoute()
const router = useRouter()

// === 响应式数据 ===
const post = ref(null)
const comments = ref([])
const loadingComments = ref(false)
const hasMoreComments = ref(true)
const totalComments = ref(0)

const commentSort = ref('hot')
const showCommentBox = ref(false)
const commentContent = ref('')
const posting = ref(false)

const inReplyMode = ref(false)
const replyTarget = ref(null)
const replyTo = ref(null)

// === 工具函数 ===
function formatTime(dateStr) {
  return formatDistanceToNow(new Date(dateStr), { locale: zhCN, addSuffix: true })
}

function goHome() { router.push('/') }
function openCreatePost() { router.push('/post/create') }

// === 获取帖子详情 ===
async function fetchPost() {
  const token = localStorage.getItem('token')
  const res = await fetch(`/api/posts/${route.params.id}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
  const data = await res.json()
  
  if (data.post?.id) {
    post.value = data.post
    totalComments.value = data.post.comment_count || 0
    loadComments(true)
  } else {
    alert('帖子不存在或已被删除')
    router.push('/')
  }
}
// === 加载评论 ===
async function loadComments(isRefresh = false) {
  if (loadingComments.value || (!hasMoreComments.value && !isRefresh)) return
  loadingComments.value = true
  if (isRefresh) {
    comments.value = []
    hasMoreComments.value = true
  }

  try {
    const token = localStorage.getItem('token')
    let url
    if (inReplyMode.value) {
      url = `/api/comments/${replyTarget.value.id}/replies?limit=10`
      if (!isRefresh && comments.value.length > 0) {
        const last = comments.value[comments.value.length - 1]
        url += `&after=${encodeURIComponent(last.created_at)}`
      }
    } else {
      url = `/api/posts/${route.params.id}/comments?sort=${commentSort.value}&limit=10`
      if (!isRefresh && comments.value.length > 0) {
        const last = comments.value[comments.value.length - 1]
        url += `&after=${encodeURIComponent(last.created_at)}`
      }
    }

    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
  const data = await res.json()
  if (Array.isArray(data.comments)) {
    const newComments = data.comments || []
    hasMoreComments.value = data.has_more !== undefined ? data.has_more : newComments.length >= 10
    if (isRefresh) {
      comments.value = newComments
    } else {
      comments.value.push(...newComments)
    }
  }
  } catch (err) {
    console.error('加载评论失败', err)
  } finally {
    loadingComments.value = false
  }
}

// === 刷新 ===
function refresh() {
  fetchPost()
}

// === 评论排序 ===
function setCommentSort(sort) {
  commentSort.value = sort
  loadComments(true)
}

// === 评论框控制 ===
function openCommentBox() {
  replyTo.value = null
  commentContent.value = ''
  showCommentBox.value = true
}

function openReplyBox(targetComment) {
  replyTo.value = targetComment.author
  commentContent.value = `@${targetComment.author.nickname} `
  showCommentBox.value = true
}

function closeCommentBox() {
  showCommentBox.value = false
  commentContent.value = ''
}

// === 提交评论（关键：带 token）===
async function submitComment() {
  if (!commentContent.value.trim()) return
  posting.value = true
  try {
    const token = localStorage.getItem('token')
    if (!token) {
      alert('请先登录')
      router.push('/login')
      return
    }

    const payload = {
      content: commentContent.value,
      parent_id: inReplyMode.value ? replyTarget.value.id : null,
      reply_to_id: replyTo.value?.id || null
    }

    const url = inReplyMode.value
      ? `/api/comments/${replyTarget.value.id}/replies`
      : `/api/posts/${route.params.id}/comments`

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    })

    // ✅ 使用 res.ok 判断成功，不再依赖 data.success
    if (res.ok) {
      closeCommentBox()
      loadComments(true)
    } else {
      const errData = await res.json().catch(() => ({}))
      if (res.status === 401) {
        alert('登录已过期，请重新登录')
        localStorage.removeItem('token')
        router.push('/login')
      } else {
        alert(errData.message || '发送失败')
      }
    }
  } catch (err) {
    console.error('提交评论出错:', err)
    alert('网络错误，请重试')
  } finally {
    posting.value = false
  }
}

// === 子评论模式 ===
function enterReplyMode(comment) {
  inReplyMode.value = true
  replyTarget.value = comment
  loadComments(true)
}

function exitReplyMode() {
  inReplyMode.value = false
  replyTarget.value = null
  loadComments(true)
}

// === 滚动加载 ===
function handleScroll() {
  if (loadingComments.value || !hasMoreComments.value) return
  const { scrollTop, scrollHeight, clientHeight } = document.documentElement
  if (scrollTop + clientHeight >= scrollHeight - 200) {
    loadComments(false)
  }
}

// === 初始化 ===
onMounted(() => {
  fetchPost()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.post-detail-container {
  min-height: 100vh;
  background-color: #f9fafb;
  position: relative;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.loading-post {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.post-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  margin-bottom: 24px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
  background: #eee;
}

.author-meta .nickname {
  font-size: 18px;
  font-weight: bold;
}
.author-meta .user-id {
  font-size: 12px;
  color: #999;
}

.post-title {
  font-size: 24px;
  font-weight: bold;
  margin: 16px 0;
}
.post-time {
  font-size: 12px;
  color: #777;
  margin-bottom: 16px;
}
.post-body {
  line-height: 1.6;
  font-size: 16px;
  color: #333;
}

.interaction-buttons {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}
.interaction-buttons button {
  padding: 6px 16px;
  border: 1px solid #ddd;
  border-radius: 20px;
  background: white;
  cursor: pointer;
}

.comments-header,
.reply-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.sort-toggle button {
  margin-left: 12px;
  padding: 4px 12px;
  border: 1px solid #ddd;
  border-radius: 16px;
  background: white;
}
.sort-toggle button.active {
  background: #4f46e5;
  color: white;
}

.reply-header .back-to-post {
  cursor: pointer;
  color: #4f46e5;
}
.reply-header .reply-target {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  margin-top: 8px;
  font-size: 14px;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  display: flex;
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.comment-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 12px;
}
.comment-content {
  flex: 1;
}
.comment-author {
  font-weight: bold;
  font-size: 14px;
}
.comment-time {
  font-size: 12px;
  color: #999;
  margin: 4px 0;
}
.comment-text {
  font-size: 14px;
  line-height: 1.5;
}

.sub-reply-preview {
  background: #f9fafb;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 8px;
  margin-top: 8px;
  cursor: pointer;
}
.hot-sub {
  font-size: 13px;
  color: #333;
}
.sub-count {
  font-size: 12px;
  color: #777;
  margin-top: 4px;
}

.comment-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.comment-actions button {
  padding: 4px 12px;
  font-size: 12px;
  border: 1px solid #ddd;
  border-radius: 16px;
  background: white;
}
.comment-actions .reply-btn {
  background: #eef2ff;
  color: #4f46e5;
}

.comment-box-overlay {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  justify-content: center;
  padding: 20px;
  z-index: 1000;
}
.comment-box {
  background: white;
  width: 100%;
  max-width: 600px;
  border-radius: 12px;
  overflow: hidden;
}
.comment-box-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  font-weight: bold;
}
.close-btn {
  font-size: 24px;
  background: none;
  border: none;
  cursor: pointer;
}
.comment-input {
  width: 100%;
  height: 120px;
  padding: 12px;
  border: none;
  resize: none;
  font-size: 14px;
}
.comment-box-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid #eee;
}
.comment-box-footer button {
  padding: 6px 16px;
  border-radius: 6px;
}
.publish-btn {
  background: #4f46e5;
  color: white;
  border: none;
}

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
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.fab.home { background: #f0f9ff; color: #0ea5e9; }
.fab.primary { background: #4f46e5; color: white; }
.fab.secondary { background: white; color: #4f46e5; }
.fab.comment { background: #dcfce7; color: #16a34a; }

.no-comments, .loading {
  text-align: center;
  padding: 24px;
  color: #777;
}

@media (max-width: 768px) {
  .main-content { padding: 12px; }
  .floating-buttons { right: 16px; }
  .comment-box { margin: 0 16px; }
}
</style>