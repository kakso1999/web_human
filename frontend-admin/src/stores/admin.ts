import { defineStore } from 'pinia'
import api from '../api'

interface AdminUser {
  id: string
  email: string
  nickname: string
  role: string
}

interface AdminState {
  user: AdminUser | null
  token: string | null
}

export const useAdminStore = defineStore('admin', {
  state: (): AdminState => ({
    user: null,
    token: localStorage.getItem('admin_token')
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isSuper: (state) => state.user?.role === 'super'
  },

  actions: {
    async login(email: string, password: string) {
      const response = await api.post('/auth/login', { email, password })
      const data = response.data.data

      // Check if user is admin or super
      if (!['admin', 'super'].includes(data.user.role)) {
        throw new Error('无管理员权限')
      }

      this.token = data.tokens.access_token
      this.user = data.user
      localStorage.setItem('admin_token', data.tokens.access_token)

      if (data.tokens.refresh_token) {
        localStorage.setItem('admin_refresh_token', data.tokens.refresh_token)
      }
    },

    async fetchProfile() {
      if (!this.token) return

      try {
        const response = await api.get('/user/profile')
        this.user = response.data.data
      } catch (error) {
        this.logout()
        throw error
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_refresh_token')
    },

    setToken(token: string) {
      this.token = token
      localStorage.setItem('admin_token', token)
    }
  }
})
