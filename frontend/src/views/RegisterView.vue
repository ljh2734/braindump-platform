<template>
  <div class="auth-container">
    <h2>📝 注册 BrainDump</h2>
    <form @submit.prevent="handleRegister" class="auth-form">
      <div class="form-group">
        <label>账号（用于登录）</label>
        <input v-model="account" type="text" required maxlength="20" placeholder="字母、数字、下划线，3-20位" />
      </div>
      <div class="form-group">
        <label>昵称</label>
        <input v-model="username" type="text" required maxlength="20" />
      </div>
      <div class="form-group">
        <label>密码（至少6位）</label>
        <input v-model="password" type="password" required minlength="6" />
      </div>
      <!-- 验证码 -->
      <div class="form-group captcha-group">
        <label>图片验证码</label>
        <div class="captcha-input-wrapper">
          <input
            v-model="captcha"
            type="text"
            required
            maxlength="6"
            placeholder="请输入验证码"
            style="width: 120px; margin-right: 10px;"
          />
          <img
            :src="captchaUrl"
            alt="验证码"
            @click="refreshCaptcha"
            style="cursor: pointer; vertical-align: middle;"
            title="点击刷新"
          />
        </div>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const account = ref('')     // 原 email，现为账号
const username = ref('')
const password = ref('')
const captcha = ref('')
const loading = ref(false)
const error = ref('')
const router = useRouter()

// 验证码相关
const captchaUrl = ref('')
const refreshCaptcha = () => {
  // 加时间戳避免缓存
  captchaUrl.value = `/api/auth/captcha?t=${new Date().getTime()}`
}
onMounted(() => {
  refreshCaptcha()
})

const handleRegister = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // 支持 session
      body: JSON.stringify({
        account: account.value.trim(),
        username: username.value.trim(),
        password: password.value,
        captcha: captcha.value.trim()
      })
    })

    const data = await response.json()
    if (response.ok) {
      alert('注册成功！请登录')
      router.push('/login')
    } else {
      error.value = data.error || '注册失败'
    }
  } catch (err) {
    console.error('注册失败:', err)
    error.value = '网络错误，请重试'
  } finally {
    loading.value = false
    refreshCaptcha() // 刷新验证码
  }
}
</script>

<style scoped>
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
.captcha-input-wrapper {
  display: flex;
  align-items: center;
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