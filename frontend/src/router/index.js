// ============================================================
//  路由配置 + 权限守卫
// ============================================================
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { roles: ['admin', 'business', 'finance', 'pm'] },
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('../views/Projects.vue'),
    meta: { roles: ['admin', 'business'] },
  },
  {
    path: '/projects/:id',
    name: 'ProjectDetail',
    component: () => import('../views/ProjectDetail.vue'),
    meta: { roles: ['admin', 'business', 'pm'] },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { roles: ['admin', 'business'] },
  },
  {
    path: '/audit',
    name: 'Audit',
    component: () => import('../views/Audit.vue'),
    meta: { roles: ['admin'] },
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../views/Users.vue'),
    meta: { roles: ['admin'] },
  },
  {
    path: '/ocr',
    name: 'OcrUpload',
    component: () => import('../views/OcrUpload.vue'),
    meta: { roles: ['admin', 'business', 'finance', 'pm'] },
  },
  {
    path: '/dict',
    name: 'Dict',
    component: () => import('../views/Dict.vue'),
    meta: { roles: ['admin'] },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: { roles: ['admin'] },
  },
]

const router = createRouter({
  history: createWebHistory('/app/'),
  routes,
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  if (to.meta.public) {
    return next()
  }

  const userStore = useUserStore()
  if (!userStore.token) {
    return next('/login')
  }

  if (!userStore.userInfo) {
    await userStore.fetchUser()
  }

  if (!userStore.userInfo) {
    return next('/login')
  }

  if (to.meta.roles && !to.meta.roles.includes(userStore.userInfo.role)) {
    return next('/dashboard')
  }

  next()
})

export default router
