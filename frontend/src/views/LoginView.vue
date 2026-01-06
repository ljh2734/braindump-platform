<template>
  <div class="login-container">
    <h2>用户登录</h2>
    <form @submit.prevent="handleLogin" class="login-form">
      <div class="form-group">
        <label for="account">账号</label>
        <input
          id="account"
          v-model="email"
          type="text"
          placeholder="请输入账号"
          required
        />
      </div>
      <div class="form-group">
        <label for="password">密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          placeholder="请输入密码"
          required
        />
      </div>
      <button type="submit" class="login-btn">登录</button>
      <p class="register-link">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/auth'
import { ElMessage } from 'element-plus'

const email = ref('')
const password = ref('')
const router = useRouter()

const handleLogin = async () => {
  if (!email.value || !password.value) {
    ElMessage({
      message: '请输入账号和密码',
      type: 'warning',
      center: true,
      duration: 2000
    })
    return
  }

  //格式校验
  const accountRegex = /^[a-zA-Z0-9_@.]{3,20}$/
  if (!accountRegex.test(email.value)) {
    ElMessage({
      message: '账号只能包含字母、数字、下划线、@、点，长度3-20位',
      type: 'warning',
      center: true,
      duration: 2000
    })
    return
  }

  try {
    const res = await login(email.value, password.value)
    const { token } = res.data
    localStorage.setItem('token', token)
    ElMessage.success('登录成功！')
    await router.push('/')
  } catch (err) {
    console.error('登录失败:', err)
    ElMessage({
      message: '登录失败，请检查账号密码',
      type: 'error',
      center: true,
      duration: 2000
    })
  }
}
</script>

<style scoped>

.el-message {
  min-width: auto !important;
  padding: 8px 16px !important;
  height: auto !important;
  line-height: 1.4 !important;
  font-size: 13px !important;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
  border-radius: 4px !important;
}

.login-container {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.login-container h2 {
  text-align: center;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

.login-btn {
  width: 100%;
  padding: 10px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.login-btn:hover {
  background-color: #337ecc;
}

.register-link {
  text-align: center;
  margin-top: 15px;
}

.register-link a {
  color: #409eff;
  text-decoration: none;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>