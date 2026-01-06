<template>
  <div class="post-create-page">
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

      <!-- 标签输入 -->
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
      <button
        @click="handleSubmit"
        :disabled="submitting"
        class="submit-btn"
      >
        {{ submitting ? '发布中...' : '发布帖子' }}
      </button>
    </div>

    <!-- 悬浮按钮（仿主页） -->
    <div class="floating-buttons">
      <button @click="goHome" class="fab primary">🏠</button>
      <button @click="resetForm" class="fab secondary">🔄</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const title = ref('')
const content = ref('')
const submitting = ref(false)
const tags = ref('')



// 跳转主页
function goHome() {
  router.push('/')
}

// 刷新 = 重置表单
function resetForm() {
  if (confirm('确定要清空所有内容吗？')) {
    title.value = ''
    content.value = ''
    tags.value = ''
  }
}

async function handleSubmit() {

  // 支持英文逗号、中文逗号、空格作为分隔符
  const tagList = tags.value
    .split(/[,，\s]+/) // 正则：匹配一个或多个 , 、 ， 或 空白字符
    .map(t => t.trim())
    .filter(t => t && t.length <= 15) // 过滤空值并确保单个标签 ≤15 字
    
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
    const res = await fetch('/api/posts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + localStorage.getItem('token')
      },
      body: JSON.stringify({
        title: title.value,
        content: content.value,
        tags: tagList
      })
    })

    const data = await res.json()
    if (data.success) {
      alert('发布成功！')
      router.push(`/post/${data.data.id}`)
    } else {
      alert(data.message || '发布失败')
    }
  } catch (err) {
    console.error(err)
    alert('网络错误，请重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.post-create-page {
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

/* 通用输入框样式 */
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

/* 标题：宽，高度不变 */
.title-input {
  height: 50px; /* 固定高度 */
}

/* 内容：宽 + 高 */
.content-input {
  min-height: 400px; /* ← 显著增高 */
  resize: vertical; /* 允许用户拖拽调整 */
  line-height: 1.5;
  /*增加右下角 padding */
  padding: 12px 16px 32px 16px; /* 上 右 下 左 */
}

/* 标签：宽，高度不变 */
.tags-input {
  height: 50px;
}

/* 提交按钮 */
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

/* 错误提示 */
.error-hint {
  color: #ef4444;
  font-size: 14px;
  margin-top: 6px;
  min-height: 18px; /* 防止布局跳动 */
}

/* 标签字数计数器 */
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