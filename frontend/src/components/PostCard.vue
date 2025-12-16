<template>
  <div class="post-card" @click="goToDetail">
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
  }
})

const router = useRouter()

// 生成内容摘要（取前 20 个字符，超出加 ...）
const excerpt = computed(() => {
  const content = props.post.content || ''
  if (content.length <= 20) return content
  return content.slice(0, 20) + '...'
})

// 跳转到详情页
function goToDetail() {
  router.push(`/post/${props.post.id}`)
}
</script>

<style scoped>
.post-card {
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

.post-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.post-excerpt {
  font-size: 14px;
  color: #4b5563;
  margin: 0 0 16px 0;
  line-height: 1.5;
  flex: 1;
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
</style>