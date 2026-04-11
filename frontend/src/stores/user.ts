import { defineStore } from 'pinia'
import api from '@/utils/request'
import type { User, UserRole } from '@/types'

interface RegisterPayload {
  username: string
  password: string
  role: 'volunteer' | 'community_admin'
  community?: number | null
}

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null as User | null,
    token: localStorage.getItem('access_token') || '',
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state): UserRole | null => state.user?.role || null,
    isAdmin: (state) => state.user?.role === 'system_admin',
    isCommunityAdmin: (state) => state.user?.role === 'community_admin',
    isVolunteer: (state) => state.user?.role === 'volunteer',
  },

  actions: {
    async login(username: string, password: string) {
      const { data } = await api.post('/users/login/', { username, password })
      this.token = data.access
      this.user = data.user
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
    },

    async register(payload: RegisterPayload) {
      const form = new FormData()
      Object.entries(payload).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          form.append(key, value as any)
        }
      })
      await api.post('/users/register/', form)
    },

    async fetchUserInfo() {
      const { data } = await api.get('/users/me/')
      this.user = data
    },

    async updateProfile(payload: Record<string, any>) {
      const form = new FormData()
      Object.entries(payload).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          form.append(key, value as any)
        }
      })
      const { data } = await api.patch('/users/update-profile/', form)
      this.user = data
    },

    logout() {
      this.user = null
      this.token = ''
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },
  },
})
