<!-- src/views/RegisterView.vue -->
<template>
  <div class="auth-container">
    <h2>📝 注册 BrainDump</h2>
    <form @submit.prevent="handleRegister" class="auth-form">
      <div class="form-group">
        <label>用户名</label>
        <input v-model="username" type="text" required maxlength="20" />
      </div>
      <div class="form-group">
        <label>邮箱</label>
        <input v-model="email" type="email" required />
      </div>
      <div class="form-group">
        <label>密码（至少6位）</label>
        <input v-model="password" type="password" required minlength="6" />
      </div>
      <button type="submit" :disabled="loading">
        {{ loading ? '注册中...' : '注册' }}
      </button>
      <p class="error" v-if="error">{{ error }}</p>
      <p class="link">已有账号？<router-link to="/login">立即登录</router-link></p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { register } from '@/api/auth'
import { useRouter } from 'vue-router'

const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const router = useRouter()

const handleRegister = async () => {
  loading.value = true
  error.value = ''
  try {
    await register(email.value, password.value, username.value)
    alert('注册成功！请登录')
    router.push('/login')
  } catch (err) {
    console.error('注册失败:', err)
    error.value = err.response?.data?.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 复用 LoginView 的样式 */
.auth-container {
  max-width: 400px;
  margin: 2rem auto;
  padding: 1.5rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}
.auth-form .form-group {
  margin-bottom: 1rem;
}
.auth-form input {
  width: 100%;
  padding: 0.5rem;
  margin-top: 0.25rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
button {
  width: 100%;
  padding: 0.5rem;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
button:disabled {
  background: #cccccc;
}
.error {
  color: red;
  margin-top: 0.5rem;
}
.link {
  margin-top: 1rem;
  text-align: center;
}
</style>
