import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

interface User {
  id: string
  email: string
  nickname: string
  avatar_url: string | null
  role: string
  is_active: boolean
}

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))

  const isLoggedIn = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const response = await api.post('/auth/login', { email, password })
    const { user: userData, tokens } = response.data.data

    user.value = userData
    token.value = tokens.access_token
    localStorage.setItem('access_token', tokens.access_token)

    return userData
  }

  async function register(email: string, password: string, nickname: string) {
    const response = await api.post('/auth/register', { email, password, nickname })
    const { user: userData, tokens } = response.data.data

    user.value = userData
    token.value = tokens.access_token
    localStorage.setItem('access_token', tokens.access_token)

    return userData
  }

  async function fetchProfile() {
    if (!token.value) return null

    try {
      const response = await api.get('/user/profile')
      user.value = response.data.data
      return user.value
    } catch (error) {
      logout()
      return null
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
  }

  async function updateProfile(data: Partial<User>) {
    const response = await api.put('/user/profile', data)
    user.value = response.data.data
    return user.value
  }

  return {
    user,
    token,
    isLoggedIn,
    login,
    register,
    fetchProfile,
    logout,
    updateProfile
  }
})
