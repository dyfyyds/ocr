// ============================================================
//  Axios 实例封装
// ============================================================
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器：注入 Token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('pm_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 跳转登录页（使用 SPA 路由，避免整页刷新到错误的 base 路径导致登录表单消失）
async function goLogin() {
  localStorage.removeItem('pm_token')
  localStorage.removeItem('pm_refresh_token')
  // 动态导入避免与 router/store 形成循环依赖
  const { default: router } = await import('../router')
  if (router.currentRoute.value.path !== '/login') {
    router.push('/login')
  }
}

// 用 access_token 过期时静默刷新，刷新成功后重放原请求
async function tryRefreshToken() {
  const refresh = localStorage.getItem('pm_refresh_token')
  if (!refresh) return null
  // 用裸 axios 调用，避免触发本拦截器造成递归
  const { data } = await axios.post('/api/auth/refresh', { refresh_token: refresh })
  localStorage.setItem('pm_token', data.access_token)
  localStorage.setItem('pm_refresh_token', data.refresh_token)
  return data.access_token
}

// 响应拦截器：统一错误处理 + 401 自动刷新
request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const { response, config } = error
    const status = response?.status

    // 401：access_token 失效。先尝试用 refresh_token 静默续期并重放一次原请求。
    const isAuthCall =
      config?.url?.includes('/auth/refresh') || config?.url?.includes('/auth/login')
    if (status === 401 && config && !config._retry && !isAuthCall) {
      config._retry = true
      try {
        const newToken = await tryRefreshToken()
        if (newToken) {
          config.headers.Authorization = `Bearer ${newToken}`
          return request(config)
        }
      } catch {
        // 刷新失败，走下面的登出逻辑
      }
      await goLogin()
      return Promise.reject(error)
    }

    if (status === 401) {
      await goLogin()
      return Promise.reject(error)
    }

    // 其它错误：统一弹出后端返回的真实原因（拦截器作为错误提示的唯一来源）
    ElMessage.error(response?.data?.message || '网络错误')
    return Promise.reject(error)
  }
)

export default request
