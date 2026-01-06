<template>
  <div class="post-edit-page">
    <div class="form-container">
      <!-- 标题输入 -->
      <div class="form-group">
        <label for="title">标题 *</label>
        <input
          id="title"
          v-model="title"
          type="text"
          class="input-field title-input"
          placeholder="请输入标题"
        />
      </div>
      <!-- 标题长度提示 -->
      <div v-if="title.length > 20" class="error-hint">
        标题不能超过 20 个字（当前 {{ title.length }} 字）
      </div>

      <!-- 内容输入 -->
      <div class="form-group">
        <label for="content">内容 *</label>
        <textarea
          id="content"
          v-model="content"
          class="input-field content-input"
          placeholder="写下你的想法..."
        ></textarea>
      </div>

      <!-- 标签输入（逗号分隔） -->
      <div class="form-group">
        <label for="tags">标签（可选，用逗号分隔）</label>
        <input
          id="tags"
          v-model="tags"
          type="text"
          class="input-field tags-input"
          placeholder="如：灵感, 设定, 写作"
        />
      </div>
      <!-- 标签字数提示 -->
      <div class="char-count" :class="{ 'over-limit': tags.length > 35 }">
        {{ tags.length }}/35
      </div>

      <!-- 提交按钮 -->
      <button @click="handleSubmit" :disabled="submitting" class="submit-btn">
        {{ submitting ? '保存中...' : '保存更改' }}
      </button>
    </div>

    <!-- 悬浮按钮 -->
    <div class="floating-buttons">
      <button @click="goHome" class="fab primary">🏠</button>
      <button @click="resetForm" class="fab secondary">🔄</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const postId = route.params.id

const title = ref('')
const content = ref('')
const tags = ref('')
const submitting = ref(false)

// 跳转主页
function goHome() {
  router.push('/')
}

// 重置表单（恢复初始值）
function resetForm() {
  if (confirm('确定要放弃更改并重置表单吗？')) {
    loadPost() // 重新加载原始数据
  }
}

// 加载原帖子
async function loadPost() {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/posts/${postId}`, {
      headers: { Authorization: 'Bearer ' + token }
    })
    if (res.ok) {
      const data = await res.json()
      title.value = data.post.title
      content.value = data.post.content
      tags.value = (data.post.tags || []).join(', ')
    } else {
      alert('无法加载帖子')
      router.push('/my-posts')
    }
  } catch (err) {
    console.error(err)
    alert('加载失败')
    router.push('/my-posts')
  }
}

// 提交更新
async function handleSubmit() {
  // 处理标签
  const tagList = tags.value
    .split(/[,，\s]+/)
    .map(t => t.trim())
    .filter(t => t && t.length <= 15)

  // 验证
  if (title.value.length > 20) {
    alert('标题不能超过 20 个字')
    return
  }
  if (!title.value.trim() || !content.value.trim()) {
    alert('标题和内容不能为空')
    return
  }
  if (tagList.some(tag => tag.length > 15)) {
    alert('每个标签不能超过15个字符')
    return
  }
  if (tags.value.length > 35) {
    alert('标签总长度不能超过 35 个字')
    return
  }

  submitting.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/posts/${postId}`, {
      method: 'PUT',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: title.value,
        content: content.value,
        tags: tagList
      })
    })

    if (res.ok) {
      alert('帖子更新成功！')
      router.push(`/post/${postId}`)
    } else {
      const err = await res.json()
      alert('更新失败：' + (err.message || '未知错误'))
    }
  } catch (err) {
    console.error(err)
    alert('网络错误，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadPost()
})
</script>

<style scoped>
.post-edit-page {
  min-height: 100vh;
  min-width: 1000px;
  background-color: #c3dcf0;
  padding: 32px 0;
  position: relative;
}

.form-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 24px;
  width: 100%;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #1f2937;
}

.input-field {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.input-field:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.title-input {
  height: 50px;
}

.content-input {
  min-height: 400px;
  resize: vertical;
  line-height: 1.5;
  padding: 12px 16px 32px 16px;
}

.tags-input {
  height: 50px;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: #4338ca;
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-hint {
  color: #ef4444;
  font-size: 14px;
  margin-top: 6px;
  min-height: 18px;
}

.char-count {
  font-size: 13px;
  color: #6b7280;
  text-align: right;
  margin-top: 0px;
  min-height: 50px;
}

.char-count.over-limit {
  color: #ef4444;
  font-weight: bold;
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
  font-size: 20px;
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
  .form-container {
    padding: 0 16px;
  }
}
</style>