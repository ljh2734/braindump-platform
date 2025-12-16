<template>
  <div class="my-posts-container">
    <h1>我的帖子</h1>
    <div v-if="loading">加载中...</div>
    <div v-else-if="posts.length === 0">你还没有发布任何帖子</div>
    <div v-else class="posts-grid">
      <PostCard
        v-for="post in posts"
        :key="post.id"
        :post="post"
      />
    </div>
    <button @click="router.go(-1)" class="back-btn">← 返回</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PostCard from '@/components/PostCard.vue'

const router = useRouter()
const posts = ref([])
const loading = ref(false)

async function loadMyPosts() {
  loading.value = true
  try {
    const res = await fetch('/api/posts?sort=newest&limit=100', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
    })
    const data = await res.json()
    if (data.success) {
      // 过滤出当前用户的帖子（后端应提供 /my-posts 接口，此处临时过滤）
      // TODO: 建议后端新增 GET /api/my-posts
      posts.value = data.data.posts.filter(p => p.author.id == JSON.parse(atob(localStorage.getItem('token').split('.')[1])).user_id)
    }
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadMyPosts()
})
</script>

<style scoped>
.my-posts-container {
  max-width: 1200px;
  margin: 24px auto;
  padding: 0 16px;
}

h1 {
  text-align: center;
  margin-bottom: 24px;
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.back-btn {
  display: block;
  margin: 24px auto 0;
  padding: 8px 16px;
  background: #f3f4f6;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
</style>