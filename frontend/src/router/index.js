import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/score/:id',
    name: 'ScoreResult',
    component: () => import('../views/ScoreResult.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/points',
    name: 'PointsLog',
    component: () => import('../views/PointsLog.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/overview' },
      { path: 'overview', name: 'AdminOverview', component: () => import('../views/admin/AdminOverview.vue') },
      { path: 'users', name: 'AdminUsers', component: () => import('../views/admin/AdminUsers.vue') },
      { path: 'models', name: 'AdminModels', component: () => import('../views/admin/AdminModels.vue') },
      { path: 'scores', name: 'AdminScores', component: () => import('../views/admin/AdminScores.vue') },
      { path: 'settings', name: 'AdminSettings', component: () => import('../views/admin/AdminSettings.vue') },
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
