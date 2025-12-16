<template>
  <div class="create-post-container">
    <header class="page-header">
      <h1>📝 新建帖子</h1>
      <button @click="goBack" class="back-btn">← 返回</button>
    </header>

    <form @submit.prevent="handleSubmit" class="post-form">
      <div class="form-group">
        <label>标题 *</label>
        <input
          v-model="title"
          type="text"
          placeholder="请输入标题（20字以内）"
          maxlength="20"
          required
          class="input-field"
        />
      </div>

      <div class="form-group">
        <label>内容 *</label>
        <textarea
          v-model="content"
          placeholder="写下你的想法..."
          rows="8"
          required
          class="textarea-field"
        ></textarea>
      </div>

      <div class="form-group">
        <label>标签（可选，用逗号分隔）</label>
        <input
          v-model="tagsInput"
          type="text"
          placeholder="如：前端,Vue,脑洞"
          class="input-field"
        />
      </div>

      <button type="submit" :disabled="submitting" class="submit-btn">
        {{ submitting ? '发布中...' : '发布帖子' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const title = ref('')
const content = ref('')
const tagsInput = ref('')
const submitting = ref(false)

function goBack() {
  router.go(-1)
}

async function handleSubmit() {
  if (!title.value.trim() || !content.value.trim()) return

  submitting.value = true
  try {
    const tags = tagsInput.value
      .split(',')
      .map(t => t.trim())
      .filter(t => t)

    const res = await fetch('/api/posts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + localStorage.getItem('token')
      },
      body: JSON.stringify({ title: title.value, content: content.value, tags })
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
.create-post-container {
  max-width: 800px;
  margin: 24px auto;
  padding: 0 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.back-btn {
  background: #e5e7eb;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #374151;
}

.input-field,
.textarea-field {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 16px;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
}

.submit-btn:disabled {
  background: #a5b4fc;
  cursor: not-allowed;
}
</style>