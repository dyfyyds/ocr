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

// 响应拦截器：统一错误处理
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || '网络错误'

    if (error.response?.status === 401) {
      localStorage.removeItem('pm_token')
      localStorage.removeItem('pm_refresh_token')
      window.location.href = '/login'
    } else {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

export default request
