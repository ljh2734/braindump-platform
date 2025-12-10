<!-- frontend/src/views/LoginView.vue -->
<template>
  <div class="login">
    <h2>登录</h2>
    <form @submit.prevent="handleSubmit">
      <input v-model="email" placeholder="邮箱" type="email" required />
      <input v-model="password" placeholder="密码" type="password" required />
      <button type="submit">登录</button>
      <p v-if="error" style="color: red">{{ error }}</p>
    </form>
    <router-link to="/">返回首页</router-link>
  </div>
</template>

<script>
import { login } from '@/api/auth'

export default {
  data() {
    return {
      email: '',
      password: '',
      error: '',
    }
  },
  methods: {
    async handleSubmit() {
      const res = await login(this.email, this.password)
      if (res.code === 200) {
        localStorage.setItem('user', JSON.stringify(res.data))
        this.$router.push('/')
      } else {
        this.error = res.message
      }
    },
  },
}
</script>
