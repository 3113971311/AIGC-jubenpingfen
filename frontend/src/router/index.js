import { createRouter, createWebHashHistory } from 'vue-router'

const SITE_NAME = '剧本评分系统'

const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true, title: '工作台' },
  },
  {
    path: '/score/:id',
    name: 'ScoreResult',
    component: () => import('../views/ScoreResult.vue'),
    meta: { requiresAuth: true, title: '评分结果' },
  },
  {
    path: '/points',
    name: 'PointsLog',
    component: () => import('../views/PointsLog.vue'),
    meta: { requiresAuth: true, title: '积分记录' },
  },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '后台管理' },
    children: [
      { path: '', redirect: '/admin/overview' },
      { path: 'overview', name: 'AdminOverview', component: () => import('../views/admin/AdminOverview.vue'), meta: { title: '概览' } },
      { path: 'users', name: 'AdminUsers', component: () => import('../views/admin/AdminUsers.vue'), meta: { title: '用户管理' } },
      { path: 'models', redirect: '/admin/settings' },
      { path: 'scores', name: 'AdminScores', component: () => import('../views/admin/AdminScores.vue'), meta: { title: '评分记录' } },
      { path: 'settings', name: 'AdminSettings', component: () => import('../views/admin/AdminSettings.vue'), meta: { title: '系统设置' } },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')

  // Update page title
  const titles = []
  if (to.meta.title) titles.push(to.meta.title)
  titles.push(SITE_NAME)
  document.title = titles.join(' - ')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.requiresAdmin && !user?.is_admin) {
    next('/dashboard')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
