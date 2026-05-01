<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isLoginPage = computed(() => route.path === '/login')

function goAdmin() {
  router.push('/admin')
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <!-- Navbar (hidden on login page) -->
  <nav v-if="!isLoginPage" class="glass-nav">
    <div class="nav-inner">
      <div class="nav-left" @click="router.push('/dashboard')" style="cursor:pointer">
        <span class="nav-logo">剧本评分</span>
      </div>
      <div class="nav-right">
        <span v-if="auth.isLoggedIn" class="nav-points glass-card" style="padding:6px 16px;border-radius:20px;cursor:pointer;" @click="router.push('/points')" title="查看积分明细">
          积分: <strong>{{ auth.points }}</strong>
        </span>
        <button v-if="auth.isAdmin" class="glass-btn" @click="goAdmin" style="padding:6px 16px;font-size:14px;">
          后台管理
        </button>
        <button v-if="auth.isLoggedIn" class="glass-btn" @click="handleLogout" style="padding:6px 16px;font-size:14px;">
          退出
        </button>
      </div>
    </div>
  </nav>

  <router-view />
</template>

<style scoped>
.glass-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(245, 245, 247, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-logo {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.3px;
  background: linear-gradient(135deg, #007aff, #5856d6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-points strong {
  color: var(--accent);
}
</style>
