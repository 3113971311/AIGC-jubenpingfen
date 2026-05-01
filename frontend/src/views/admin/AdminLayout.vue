<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const mobileOpen = ref(false)

const menuItems = [
  { path: '/admin/overview', label: '概览', icon: 'DataAnalysis' },
  { path: '/admin/users', label: '用户管理', icon: 'User' },
  { path: '/admin/models', label: '模型配置', icon: 'Setting' },
  { path: '/admin/scores', label: '评分记录', icon: 'Document' },
  { path: '/admin/settings', label: '系统设置', icon: 'Tools' },
]

const activeIndex = computed(() => {
  const idx = menuItems.findIndex(m => route.path.startsWith(m.path))
  return idx >= 0 ? String(idx) : '0'
})

const currentLabel = computed(() => {
  const item = menuItems.find(m => route.path.startsWith(m.path))
  return item?.label || ''
})

function onSelect(index) {
  router.push(menuItems[Number(index)].path)
  mobileOpen.value = false
}
</script>

<template>
  <div class="admin-layout" :class="{ collapsed }">
    <!-- Sidebar -->
    <aside class="admin-sidebar glass-panel" :class="{ 'mobile-open': mobileOpen }">
      <div class="sidebar-header" @click="router.push('/dashboard')">
        <el-icon :size="22" class="sidebar-logo-icon"><VideoCamera /></el-icon>
        <span v-show="!collapsed || mobileOpen" class="sidebar-logo-text">剧本评分</span>
      </div>

      <el-menu :default-active="activeIndex" @select="onSelect" :collapse="collapsed && !mobileOpen">
        <el-menu-item v-for="(item, i) in menuItems" :key="i" :index="String(i)">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <button class="collapse-btn" @click="collapsed = !collapsed" title="收起/展开侧边栏">
          <el-icon :size="18"><component :is="collapsed ? 'Expand' : 'Fold'" /></el-icon>
        </button>
      </div>
    </aside>

    <!-- Main -->
    <main class="admin-main">
      <div class="admin-topbar">
        <div class="topbar-left">
          <button class="mobile-menu-btn" @click="mobileOpen = true">
            <el-icon :size="20"><Menu /></el-icon>
          </button>
          <h1 class="admin-page-title">{{ currentLabel }}</h1>
        </div>
      </div>
      <div class="admin-content">
        <router-view />
      </div>
    </main>

    <!-- Mobile overlay -->
    <div v-if="mobileOpen" class="mobile-overlay" @click="mobileOpen = false" />
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  min-height: calc(100vh - 57px);
}

/* ===== Sidebar ===== */
.admin-sidebar {
  width: 230px;
  flex-shrink: 0;
  margin: 16px;
  padding: 16px 0;
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 73px;
  height: calc(100vh - 89px);
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  z-index: 100;
}

.collapsed .admin-sidebar {
  width: 72px;
}

.collapsed .admin-sidebar .sidebar-logo-text,
.collapsed .admin-sidebar .el-menu-item span {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 20px 16px;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  cursor: pointer;
  white-space: nowrap;
}

.collapsed .sidebar-header {
  justify-content: center;
  padding: 4px 0 16px;
}

.sidebar-logo-icon {
  color: var(--accent);
  flex-shrink: 0;
}

.sidebar-logo-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
  background: linear-gradient(135deg, #007aff, #5856d6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  transition: opacity 0.2s;
}

/* ===== Menu ===== */
.el-menu {
  background: transparent !important;
  border: none !important;
  flex: 1;
  padding: 4px 12px;
}

.collapsed .el-menu {
  padding: 4px 8px;
}

.el-menu-item {
  border-radius: 12px;
  margin-bottom: 2px;
  height: 44px;
  line-height: 44px;
  transition: all 0.2s ease;
}

.el-menu-item:hover {
  background: rgba(0, 122, 255, 0.06) !important;
}

.el-menu-item.is-active {
  background: rgba(0, 122, 255, 0.1) !important;
  color: var(--accent) !important;
  font-weight: 600;
}

/* ===== Footer ===== */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: center;
}

.collapse-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.collapse-btn:hover {
  background: rgba(0, 122, 255, 0.08);
  color: var(--accent);
}

/* ===== Main ===== */
.admin-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.admin-topbar {
  padding: 20px 24px 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-page-title {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.mobile-menu-btn {
  display: none;
  padding: 6px 10px;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--text-primary);
  border-radius: 8px;
}

.mobile-menu-btn:hover {
  background: rgba(0, 0, 0, 0.04);
}

.admin-content {
  flex: 1;
  padding: 20px 24px 40px;
  min-width: 0;
}

.mobile-overlay {
  display: none;
}

/* ===== Mobile ===== */
@media (max-width: 768px) {
  .admin-sidebar {
    position: fixed;
    left: 0;
    top: 57px;
    bottom: 0;
    margin: 8px;
    border-radius: var(--radius-lg);
    transform: translateX(-260px);
    width: 240px !important;
    z-index: 200;
    box-shadow: 0 25px 70px rgba(0, 0, 0, 0.2);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .admin-sidebar.mobile-open {
    transform: translateX(0);
  }

  .admin-sidebar .sidebar-logo-text,
  .admin-sidebar .el-menu-item span {
    opacity: 1;
    width: auto;
    overflow: visible;
  }

  .admin-sidebar .sidebar-header {
    justify-content: flex-start;
    padding: 4px 20px 16px;
  }

  .admin-sidebar .el-menu {
    padding: 4px 12px;
  }

  .mobile-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.25);
    z-index: 150;
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
  }

  .mobile-menu-btn {
    display: flex;
  }

  .admin-topbar {
    padding: 12px 16px 0;
  }

  .admin-content {
    padding: 16px;
  }

  .admin-page-title {
    font-size: 22px;
  }

  .sidebar-footer {
    display: none;
  }

  /* Don't collapse on mobile */
  .collapsed .admin-sidebar {
    width: 240px !important;
  }
}
</style>
