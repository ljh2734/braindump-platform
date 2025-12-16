<template>
  <div class="search-container">
    <h2>搜索结果：{{ query }}</h2>
    <!-- 此处可调用 /api/search?q=...，但你目前只有标签搜索 -->
    <p>暂未实现关键词全文搜索，可前往「标签搜索」</p>
    <button @click="router.push('/search/tags')">按标签搜索</button>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const query = route.query.q || ''
</script>

<style scoped>
.search-container {
  text-align: center;
  padding: 40px;
}
</style>