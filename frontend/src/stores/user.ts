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
    // 仅持久化 token；用户详情在刷新后通过 /users/me/ 恢复。
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
      // 登录成功后保存 access/refresh token，并缓存用户信息。
      const { data } = await api.post('/users/login/', { username, password })
      this.token = data.access
      this.user = data.user
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
    },

    async register(payload: RegisterPayload) {
      // 注册接口使用 FormData，兼容后续扩展上传字段。
      const form = new FormData()
      Object.entries(payload).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          form.append(key, value as any)
        }
      })
      await api.post('/users/register/', form)
    },

    async fetchUserInfo() {
      // 根据当前 token 拉取 /users/me/，用于刷新页面后的用户态恢复。
      const { data } = await api.get('/users/me/')
      this.user = data
    },

    async updateProfile(payload: Record<string, any>) {
      // 资料更新包含头像文件，统一走 FormData。
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
      // 统一清理所有本地登录态信息。
      this.user = null
      this.token = ''
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },
  },
})
