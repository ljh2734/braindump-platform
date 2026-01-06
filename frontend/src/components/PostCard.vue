<template>
  <div class="post-card" @click="goToDetail">

    <!-- 删除和编辑按钮（仅作者可见） -->
    <div v-if="isAuthor" class="action-buttons">
      <button @click.stop="editPost" class="edit-btn" title="编辑帖子">✏️</button>
      <button @click.stop="deletePost" class="delete-btn" title="删除帖子">🗑️</button>
    </div>

    <!-- 标题 -->
    <h3 class="post-title">{{ post.title }}</h3>

    <!-- 内容摘要 -->
    <p class="post-excerpt">
      {{ excerpt }}
    </p>

    <!-- 底部统计栏 -->
    <div class="post-stats">
      <span class="stat-item">
        💬 {{ post.comment_count || 0 }}
      </span>
      <span class="stat-item">
        👍 {{ post.like_count || 0 }}
      </span>
      <span class="stat-item">
        ❓ {{ post.question_count || 0 }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  post: {
    type: Object,
    required: true,
    validator(value) {
      return value && typeof value.id !== 'undefined'
    }
  },
  currentUserId: { type: [Number, null], default: null }
})

const router = useRouter()
const emit = defineEmits(['deleted']) 

// 生成内容摘要（取前 20 个字符，超出加 ...）
const excerpt = computed(() => {
  const content = props.post.content || ''
  if (content.length <= 20) return content
  return content.slice(0, 20) + '...'
})

// 判断当前用户是否为帖子作者
const isAuthor = computed(() => {
  return props.currentUserId && props.post.author?.id === props.currentUserId
})

// 跳转到详情页
function goToDetail() {
  router.push(`/post/${props.post.id}`)
}

function editPost() {
  router.push(`/post/edit/${props.post.id}`)
}

async function deletePost() {
  if (!confirm('确定要删除这篇帖子吗？')) return

  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/posts/${props.post.id}`, {
      method: 'DELETE',
      headers: { Authorization: 'Bearer ' + token }
    })

    if (res.ok) {
      alert('帖子已删除')
      emit('deleted', props.post.id) // 通知父组件
    } else {
      const err = await res.json()
      alert('删除失败：' + (err.error || '未知错误'))
    }
  } catch (err) {
    console.error(err)
    alert('网络错误，请重试')
  }
}

</script>

<style scoped>
.post-card {
  width: 100%;
  min-width: 0;
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.post-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}

.post-title,
.post-excerpt {
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  hyphens: auto;
}

.post-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #6b7280;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}



.delete-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

.action-buttons {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.post-card:hover .action-buttons {
  opacity: 1;
}

.edit-btn,
.delete-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e5e7eb;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.2s;
}

.edit-btn:hover {
  background: #e0f2fe;
  color: #0ea5e9;
}

.delete-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}
</style>