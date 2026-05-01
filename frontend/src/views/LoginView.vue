<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) return
  loading.value = true
  try {
    const res = await login({ username: username.value, password: password.value })
    auth.setAuth(res.data.access_token, res.data.user)
    router.push('/dashboard')
  } catch {} finally { loading.value = false }
}
</script>

<template>
  <div class="login-page">
    <div class="login-bg-decor" />
    <div class="login-card glass-card glass-card-strong">
      <div class="login-icon"><el-icon :size="40"><VideoCamera /></el-icon></div>
      <h1 class="login-title">剧本评分系统</h1>
      <p class="login-subtitle">AI 驱动的专业剧本分析</p>
      <div class="login-form">
        <el-input v-model="username" placeholder="用户名" size="large" @keyup.enter="handleLogin" />
        <el-input v-model="password" type="password" placeholder="密码" size="large" show-password @keyup.enter="handleLogin" />
        <el-button type="primary" size="large" :loading="loading" @click="handleLogin" round style="width:100%;">
          {{ loading ? '登录中...' : '登录' }}
        </el-button>
      </div>
      <p class="login-hint">账号由管理员创建和发放</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.login-bg-decor {
  position: fixed; inset: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 70% 50% at 30% 30%, rgba(0,122,255,0.1), transparent),
    radial-gradient(ellipse 50% 60% at 70% 70%, rgba(88,86,214,0.08), transparent);
}
.login-card {
  width: 400px; max-width: 100%; padding: 48px 36px; text-align: center; position: relative;
}
.login-icon { margin-bottom: 16px; color: var(--accent); display: flex; justify-content: center; }
.login-title { font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 8px; }
.login-subtitle { font-size: 15px; color: var(--text-secondary); margin-bottom: 32px; }
.login-form { display: flex; flex-direction: column; gap: 14px; }
.login-hint { font-size: 13px; color: var(--text-tertiary); margin-top: 20px; }

@media (max-width: 480px) {
  .login-card { padding: 36px 24px; }
  .login-title { font-size: 24px; }
}
</style>
