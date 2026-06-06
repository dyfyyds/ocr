// ============================================================
//  用户状态管理
// ============================================================
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getMe } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('pm_token') || '')
  const refreshToken = ref(localStorage.getItem('pm_refresh_token') || '')
  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username, password) {
    const res = await loginApi(username, password)
    token.value = res.access_token
    refreshToken.value = res.refresh_token
    userInfo.value = res.user

    localStorage.setItem('pm_token', res.access_token)
    localStorage.setItem('pm_refresh_token', res.refresh_token)
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await getMe()
      userInfo.value = res
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem('pm_token')
    localStorage.removeItem('pm_refresh_token')
  }

  return { token, refreshToken, userInfo, isLoggedIn, login, fetchUser, logout }
})
