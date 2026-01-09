import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { authApi, userApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isSubscriber = computed(() => user.value?.role === 'subscriber' || user.value?.role === 'admin')

  // 初始化用户信息
  async function init() {
    const token = localStorage.getItem('access_token')
    if (token && !user.value) {
      try {
        await fetchProfile()
      } catch (e) {
        logout()
      }
    }
  }

  // 获取用户信息
  async function fetchProfile() {
    loading.value = true
    try {
      const res = await userApi.getProfile()
      user.value = res.data
    } finally {
      loading.value = false
    }
  }

  // 登录
  async function login(email: string, password: string) {
    loading.value = true
    try {
      const res = await authApi.login({ email, password })
      localStorage.setItem('access_token', res.data.tokens.access_token)
      localStorage.setItem('refresh_token', res.data.tokens.refresh_token)
      user.value = res.data.user
      return res
    } finally {
      loading.value = false
    }
  }

  // 注册
  async function register(email: string, password: string, nickname: string) {
    loading.value = true
    try {
      const res = await authApi.register({ email, password, nickname })
      localStorage.setItem('access_token', res.data.tokens.access_token)
      localStorage.setItem('refresh_token', res.data.tokens.refresh_token)
      user.value = res.data.user
      return res
    } finally {
      loading.value = false
    }
  }

  // Google 登录
  async function googleLogin(code: string) {
    loading.value = true
    try {
      const res = await authApi.googleAuth(code)
      localStorage.setItem('access_token', res.data.tokens.access_token)
      localStorage.setItem('refresh_token', res.data.tokens.refresh_token)
      user.value = res.data.user
      return res
    } finally {
      loading.value = false
    }
  }

  // 登出
  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    user.value = null
  }

  // 更新用户信息
  async function updateProfile(data: { nickname?: string }) {
    const res = await userApi.updateProfile(data)
    user.value = res.data
  }

  return {
    user,
    loading,
    isLoggedIn,
    isAdmin,
    isSubscriber,
    init,
    fetchProfile,
    login,
    register,
    googleLogin,
    logout,
    updateProfile
  }
})
