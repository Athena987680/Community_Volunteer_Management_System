import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'
const API_ORIGIN = new URL(API_BASE_URL).origin

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
})

export const asList = <T>(payload: any): T[] => {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.results)) return payload.results
  return []
}

const toMediaUrl = (value: string) => {
  if (!value) return value
  if (value.startsWith('http://') || value.startsWith('https://') || value.startsWith('blob:') || value.startsWith('data:')) {
    return value
  }
  if (value.startsWith('/media/')) {
    return `${API_ORIGIN}${value}`
  }
  if (value.startsWith('media/')) {
    return `${API_ORIGIN}/${value}`
  }
  return value
}

const normalizeMediaUrls = (payload: any): any => {
  if (Array.isArray(payload)) {
    return payload.map(item => normalizeMediaUrls(item))
  }
  if (!payload || typeof payload !== 'object') {
    return payload
  }

  const next = { ...payload }
  Object.keys(next).forEach(key => {
    const value = next[key]
    if (typeof value === 'string' && (key === 'avatar' || key === 'cover_image')) {
      next[key] = toMediaUrl(value)
      return
    }
    next[key] = normalizeMediaUrls(value)
  })

  return next
}

api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error),
)

api.interceptors.response.use(
  response => {
    response.data = normalizeMediaUrls(response.data)
    return response
  },
  async error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export default api
