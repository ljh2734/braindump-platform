<template>
  <div class="post-detail-container">
    <!-- 右侧悬浮按钮 -->
    <div class="floating-buttons">
      <button @click="goHome" class="fab home">🏠</button>
      <button @click="openCreatePost" class="fab primary">📝</button>
      <button @click="refresh" class="fab secondary">🔄</button>
      <button @click="openCommentBoxInContext" class="fab comment">💬</button>
    </div>

    <main class="main-content">
      <!-- 帖子内容区 -->
      <div v-if="post" class="post-card">
          <div class="author-info">
          <img 
            :src="userAvatar" 
            alt="头像" 
            class="avatar clickable" 
            @click="handleAuthorAvatarClick"
          />
          <div class="author-meta">
            <div class="username">{{ post.author.username }}</div>
            <div class="user-id">@{{ post.author.id }}</div>
          </div>
        </div>

        <h1 class="post-title">{{ post.title }}</h1>
        <div class="post-time">{{ formatTime(post.created_at) }}</div>
        <div class="post-body" v-html="post.content"></div>

        <div class="interaction-buttons">
            <button class="like-btn" @click="likePost">👍 {{ post.like_count || 0 }}</button>
            <button class="question-btn" @click="questionPost">❓ {{ post.question_count || 0 }}</button>
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
          <strong>{{ replyTarget?.author?.username }}</strong>
          <p>{{ replyTarget?.content }}</p>
        </div>
      </div>

  <!-- 评论列表 -->
  <div class="comments-list" ref="commentsContainer">
    <div v-for="comment in comments" :key="comment.id" class="comment-item">
      <img 
        :src="commentAuthorAvatar(comment)" 
        alt="评论者头像" 
        class="comment-avatar clickable" 
        @click="handleCommentAvatarClick(comment)"
      />
      <div class="comment-content">
        <div class="comment-author">{{ comment.author.username }}</div>
        <div class="comment-time">{{ formatTime(comment.created_at) }}</div>
        <div class="comment-text">{{ comment.content }}</div>
      </div>

      <!-- 最热子评论预览块 -->
      <div v-if="!inReplyMode && comment.hot_reply" 
          class="hot-reply-preview" 
          @click="enterReplyMode(comment)">
        {{ comment.hot_reply.content }}
      </div>

      <!-- 互动按钮 -->
      <div class="comment-actions">
        <button class="like-btn small" @click="likeComment(comment.id)">👍 {{ comment.like_count || 0 }}</button>
        <button class="question-btn small" @click="questionComment(comment.id)">❓ {{ comment.question_count || 0 }}</button>
        <button class="reply-btn small" @click="handleReplyClick(comment)">
        💬 
        <!-- 只在主评论区显示计数 -->
        <span v-if="!inReplyMode">{{ comment.sub_count || 0 }}</span>
        </button>
      </div>
    </div>
    
    <!-- 全局状态提示 -->
    <div v-if="loadingComments && comments.length === 0" class="loading">加载评论中...</div>
    <div v-else-if="comments.length === 0" class="no-comments">{{ inReplyMode ? '暂无回复' : '暂无评论' }}</div>
    <div v-if="!hasMoreComments && comments.length > 0" class="no-more-comments">已显示全部 {{ comments.length }} 条评论</div>
  </div>
    </main>

    <!-- 底部评论框 -->
    <div v-if="showCommentBox" class="comment-box-overlay">
      <div class="comment-box">
        <div class="comment-box-header">
          <span>{{ inReplyMode ? `回复 ${replyTarget?.author?.username}` : '发表评论' }}</span>
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
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
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

// 用于控制“当前展示多少条”
const displayedCount = ref(0)
const batchSize = 10 // 每次滚动加载多少条
const currentUser = ref(null)
const commentSort = ref('hot')
const showCommentBox = ref(false)
const commentContent = ref('')
const posting = ref(false)

const inReplyMode = ref(false)
const replyTarget = ref(null)
const replyTo = ref(null)
const DEFAULT_AVATAR = '/static/default-avatar.png'
// 帖子作者头像
const userAvatar = computed(() => {
  return post.value?.author?.avatar_url || DEFAULT_AVATAR
})

// 评论头像
const commentAuthorAvatar = (comment) => {
  return comment.author?.avatar_url || DEFAULT_AVATAR
}

async function fetchCurrentUser() {
  const token = localStorage.getItem('token')
  if (!token) {
    currentUser.value = null
    return
  }

  try {
    const res = await fetch('/api/user/me', {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.ok) {
      const userData = await res.json()
      currentUser.value = userData
    } else {
      currentUser.value = null
      //token 无效时清除
      localStorage.removeItem('token')
    }
  } catch (error) {
    console.error('Fetch current user failed:', error)
    currentUser.value = null
  }
}

// === 私信 ===
function goToChat(userId) {
  if (!userId) return;
  router.push(`/messages/${userId}`)
}

function handleAuthorAvatarClick() {
  if (!currentUser.value || !post.value?.author?.id) return
  if (currentUser.value.id !== post.value.author.id) {
    goToChat(post.value.author.id)
  }
}

function handleCommentAvatarClick(comment) {
  if (!currentUser.value || !comment.author?.id) return
  if (currentUser.value.id !== comment.author.id) {
    goToChat(comment.author.id)
  }
}


// === 工具函数 ===
function formatTime(dateStr) {
  return formatDistanceToNow(new Date(dateStr), { locale: zhCN, addSuffix: true })
}

function goHome() { router.push('/') }
function openCreatePost() { router.push('/post/create') }

// === 获取帖子详情 ===
async function fetchPost() {
  const token = localStorage.getItem('token');
  
  if (!route.params.id || !Number.isInteger(Number(route.params.id))) {
    alert('帖子 ID 无效');
    router.push('/');
    return;
  }

  const postId = Number(route.params.id);
  const params = new URLSearchParams({
    comment_sort: commentSort.value,
    limit: '200'
  });
  const url = `/api/posts/${postId}?${params.toString()}`;

  try {
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });

    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

    const data = await res.json();

  if (data.post?.id) {
    post.value = data.post;
    
    // 只取 parent_id 为 null 的评论（主评论）
    const allComments = data.comments || [];
    const mainComments = allComments.filter(c => c.parent_id === null);

    mainComments.forEach(c => {
      // 确保 sub_count 存在
      if (c.sub_count === undefined) {
        c.sub_count = 0;
      }
      // 如果后端不提供 hot_reply，再用前端逻辑
      if (c.hot_reply === undefined) {
        const subs = allComments.filter(child => child.parent_id === c.id);
        c.hot_reply = subs.length > 0 ? subs[0] : null;
      }
    });

    totalComments.value = mainComments.length;
    comments.value = mainComments.map(comment => {
      if (!comment.author) {
        comment.author = { 
          id: comment.user_id, 
          username: '匿名用户', 
          avatar_url: DEFAULT_AVATAR 
        };
      }
      return comment;
    });
    displayedCount.value = Math.min(batchSize, comments.value.length);
    hasMoreComments.value = comments.value.length > batchSize;
  } else {
      alert('帖子不存在或已被删除');
      router.push('/');
    }
  } catch (error) {
    console.error('Fetch failed:', error);
    alert('加载失败，请稍后再试');
  }
}

// === 获取子评论 ===
async function fetchSubComments(parentId) {
  const token = localStorage.getItem('token');
  loadingComments.value = true;
  try {
    const res = await fetch(`/api/top-level/${parentId}/replies`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();
    
    comments.value = (data.replies || []).map(reply => {
      if (!reply.author) {
        reply.author = { username: '匿名用户', avatar_url: DEFAULT_AVATAR };
      }
      return reply;
    });
    
    displayedCount.value = comments.value.length; // 子评论不分页
    hasMoreComments.value = false;
    totalComments.value = comments.value.length; // 更新标题数字
  } catch (error) {
    console.error('Fetch sub-comments failed:', error);
    comments.value = [];
    alert('加载回复失败，请稍后再试');
  } finally {
    loadingComments.value = false;
  }
}

// “展示中的评论”计算属性
const displayedComments = computed(() => {
  return comments.value.slice(0, displayedCount.value);
});

// === 刷新 ===
function refresh() {
  displayedCount.value = 0; // 重置展示计数
  if (inReplyMode.value && replyTarget.value?.id) {
    // 子评论区：刷新当前子评论
    fetchSubComments(replyTarget.value.id);
  } else {
    // 主评论区：刷新主评论
    fetchPost();
  }
}
// === 评论排序 ===
function setCommentSort(sort) {
  commentSort.value = sort
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

function openCommentBoxInContext() {
  if (inReplyMode.value) {
    // 子评论区：默认回复顶部的主评论
    replyTo.value = replyTarget.value?.author;
    commentContent.value = replyTarget.value?.author 
      ? `@${replyTarget.value.author.username} ` 
      : '';
  } else {
    // 主评论区：普通评论
    replyTo.value = null;
    commentContent.value = '';
  }
  showCommentBox.value = true;
}

function closeCommentBox() {
  showCommentBox.value = false
  commentContent.value = ''
}

// === 提交评论（带 token）===
async function submitComment() {
  const token = localStorage.getItem('token');
  if (!token) {
    alert('请先登录');
    router.push('/login');
    return;
  }

  const content = commentContent.value.trim();
  if (!content) {
    alert('评论内容不能为空');
    return;
  }

  try {
    posting.value = true;

    // 构建请求体
    const requestBody = { content };
    if (inReplyMode.value && replyTarget.value?.id) {
      requestBody.parent_id = replyTarget.value.id;
    }

    // 发起请求
    const res = await fetch(`/api/posts/${route.params.id}/comments`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody) //使用已构建好的 requestBody
    });

    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

    const newComment = await res.json();

    if (inReplyMode.value) {
      comments.value.push(newComment); // 子评论区：追加
    } else {
      comments.value.unshift(newComment); // 主评论区：置顶
    }

    commentContent.value = '';
    showCommentBox.value = false;
    displayedCount.value = Math.min(displayedCount.value + 1, comments.value.length);

  } catch (error) {
    console.error('Submit failed:', error);
    alert('提交失败，请重试');
  } finally {
    posting.value = false;
  }
}

// === 帖子互动 ===
async function likePost() {
  const token = localStorage.getItem('token');
  if (!token) {
    alert('请先登录');
    router.push('/login');
    return;
  }
  
  try {
    const res = await fetch(`/api/posts/${post.value.id}/like`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    
    const data = await res.json();
    if (data.count !== undefined) {
      post.value.like_count = data.count;
    }
  } catch (error) {
    console.error('Like failed:', error);
  }
}

async function questionPost() {
  const token = localStorage.getItem('token');
  if (!token) {
    alert('请先登录');
    router.push('/login');
    return;
  }
  
  try {
    const res = await fetch(`/api/posts/${post.value.id}/question`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    
    const data = await res.json();
    if (data.count !== undefined) {
      post.value.question_count = data.count;
    }
  } catch (error) {
    console.error('Question failed:', error);
  }
}

// === 评论互动 ===
// 修改 likeComment
async function likeComment(commentId) {
  const token = localStorage.getItem('token');
  if (!token) {
    alert('请先登录');
    router.push('/login');
    return;
  }
  try {
    const res = await fetch(`/api/comments/${commentId}/like`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    if (data.count !== undefined) {
      // 通过 id 查找
      const comment = comments.value.find(c => c.id === commentId);
      if (comment) comment.like_count = data.count;
    }
  } catch (error) {
    console.error('Like failed:', error);
  }
}

async function questionComment(commentId) {
  const token = localStorage.getItem('token');
  if (!token) {
    alert('请先登录');
    router.push('/login');
    return;
  }
  try {
    const res = await fetch(`/api/comments/${commentId}/question`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    if (data.count !== undefined) {
      const comment = comments.value.find(c => c.id === commentId);
      if (comment) comment.question_count = data.count;
    }
  } catch (error) {
    console.error('Question failed:', error);
  }
}
// === 子评论模式 ===
function enterReplyMode(comment) {
  inReplyMode.value = true
  replyTarget.value = comment
}


function handleReplyClick(comment) {
  if (inReplyMode.value) {
    // 在子评论区：打开评论框并 @ 用户
    replyTo.value = comment.author;
    commentContent.value = `@${comment.author.username} `;
    showCommentBox.value = true;
  } else {
    // 在主评论区：进入子评论详情页
    inReplyMode.value = true;
    replyTarget.value = comment;
    fetchSubComments(comment.id);
  }
}

function exitReplyMode() {
  inReplyMode.value = false;
  replyTarget.value = null;
  // 重新加载主评论（从缓存或重新请求）
  fetchPost();
}

// === 滚动加载 ===
function handleScroll() {
  const container = document.querySelector('.main-content');
  if (!container) return;

  const isAtBottom = container.scrollHeight - window.scrollY <= window.innerHeight + 100;
  if (!isAtBottom) return;

  if (loadingComments.value || displayedCount.value >= comments.value.length) {
    return;
  }

  displayedCount.value = Math.min(
    displayedCount.value + batchSize,
    comments.value.length
  );

  if (displayedCount.value >= comments.value.length) {
    hasMoreComments.value = false;
  }
}

watch(commentSort, () => {
  displayedCount.value = 0; // 重置展示计数
  fetchPost();             // 重新加载新排序的数据
});

// === 初始化 ===
onMounted(() => {
  fetchPost()
  fetchCurrentUser()
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
  width: 1000px;        /* 固定宽度 */
  margin: 0 auto;
  padding: 24px;
  background: rgb(166, 228, 235); 
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

.loading-post {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.post-card {
   max-width: 1000px;
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
  /* 强制换行 */
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}
.post-time {
  font-size: 12px;
  color: #777;
  margin-bottom: 16px;
}
/* 帖子正文 */
.post-body {
  white-space: pre-line;
  line-height: 1.6;
  font-size: 16px;
  color: #333;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}
.post-body :deep(*) {
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
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
  background: #569cde;
  color: white;
}

.reply-header .back-to-post {
  cursor: pointer;
  color: #5e8dbf;
}
.reply-header .reply-target {
  background: #a0cdf2;
  padding: 12px;
  border-radius: 8px;
  margin-top: 8px;
  font-size: 14px;
  width:90%;
  max-width: none;
  box-sizing: border-box;
  white-space: normal;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 评论项 */
.comment-item {
  width: 100%;   /* 占满 */
  background: rgb(255, 255, 255);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  display: flex;
    align-items: flex-start; /* 文本和按钮顶部对齐 */
  gap: 12px;
}
.comment-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 12px;
}
.comment-content {
  flex: 1;
  min-width: 0;
  max-width: 400px;
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
  white-space: pre-line;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  hyphens: auto;
  min-width: 0;
}
.sub-reply-preview {
  flex: 1;
  max-width: none;
  margin: 8px 0 0 60px; /* 左侧留出头像空间 */
  padding: 10px 14px;
  background: #f9fafb;
  border: 1px solid #eee;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #555;
}

.hot-sub {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  white-space: nowrap; /* 防止换行 */
}

.reply-to {
  font-weight: 500;
  color: #666;
  flex-shrink: 0; /* 不收缩 */
}

.hot-sub {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  white-space: nowrap; /* 防止换行 */
}
/* 内容过长时显示省略号 */
.hot-sub > :nth-child(2) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sub-count {
  font-size: 12px;
  color: #777;
  margin-top: 4px;
}

.comment-actions {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-self: flex-start; /* 保持顶部对齐 */
  margin-left: auto; /* 推到最右侧 */
}
.comment-actions button {
  padding: 6px 12px;
  min-height: 28px;
  font-size: 12px;
  border: 1px solid #ddd;
  border-radius: 20px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  white-space: nowrap; /* 防止换行 */
}



.comment-actions .reply-btn {
  background: #eef2ff;
  color: #67c0d0;
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

.no-more-comments {
  text-align: center;
  color: #999;
  padding: 16px;
  font-size: 14px;
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

/*最热子评论展示*/
.hot-reply-preview {
  margin-top: 8px;
  padding: 10px 14px;
  background: #f9fafb;
  border: 1px solid #eee;
  border-radius: 8px;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  max-width: 350px;
  width: 100%;
  box-sizing: border-box;
  /* 超出省略 */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.send-message-btn {
  margin-top: 8px;
  padding: 4px 12px;
  background: #e0f2fe;
  color: #0ea5e9;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.avatar.clickable,
.comment-avatar.clickable {
  cursor: pointer;
  transition: transform 0.2s;
}
.avatar.clickable:hover,
.comment-avatar.clickable:hover {
  transform: scale(1.05);
}

@media (max-width: 768px) {
  .main-content { padding: 12px; }
  .floating-buttons { right: 16px; }
  .comment-box { margin: 0 16px; }
}
</style>