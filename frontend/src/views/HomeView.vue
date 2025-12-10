<!-- frontend/src/views/HomeView.vue -->
<template>
  <div class="home">
    <h1>脑洞分享平台</h1>
    <p v-if="!isLoggedIn">欢迎！请先登录以发布你的奇思妙想。</p>
    <p v-else>你好，{{ username }}！你可以开始发布脑洞了。</p>
    <router-link to="/login" v-if="!isLoggedIn">去登录</router-link>
    <button @click="handleLogout" v-else>退出登录</button>
  </div>
</template>

<script>
import { logout } from '@/api/auth'

export default {
  data() {
    return {
      isLoggedIn: false,
      username: '',
    }
  },
  async mounted() {
    // 简单判断：尝试访问一个需要登录的接口，或从本地状态读取
    // 此处简化：刷新页面后状态丢失（后续可用 /me 接口）
    const userStr = localStorage.getItem('user')
    if (userStr) {
      const user = JSON.parse(userStr)
      this.isLoggedIn = true
      this.username = user.username
    }
  },
  methods: {
    async handleLogout() {
      await logout()
      localStorage.removeItem('user')
      this.isLoggedIn = false
      this.username = ''
      this.$router.push('/')
    },
  },
}
</script>
