import axios from 'axios'

// 支持通过环境变量切换后端地址；未配置时默认走同域代理 /api。
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const API_ORIGIN = (() => {
  // 配置为绝对地址时提取其源；相对地址走当前页面源。
  if (/^https?:\/\//i.test(API_BASE_URL)) {
    return new URL(API_BASE_URL).origin
  }
  if (typeof window !== 'undefined') {
    return window.location.origin
  }
  return ''
})()

const api = axios.create({
  baseURL: API_BASE_URL,
  // 避免弱网场景请求长时间挂起。
  timeout: 15000,
})

// 兼容后端返回数组或分页对象两种列表结构。
export const asList = <T>(payload: any): T[] => {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.results)) return payload.results
  return []
}

// 将媒体路径统一转换为当前可访问的完整地址。
const toMediaUrl = (value: string) => {
  if (!value) return value
  // 本地临时地址不做转换。
  if (value.startsWith('blob:') || value.startsWith('data:')) {
    return value
  }
  if (value.startsWith('http://') || value.startsWith('https://')) {
    try {
      const parsed = new URL(value)
      if (parsed.pathname.startsWith('/media/')) {
        const isLocalLoopHost = ['127.0.0.1', 'localhost', '0.0.0.0'].includes(parsed.hostname)
        // 后端返回 localhost 媒体地址时，优先替换为当前前端域名，避免跨端口不可达。
        if (typeof window !== 'undefined' && (isLocalLoopHost || API_BASE_URL.startsWith('/'))) {
          return `${window.location.origin}${parsed.pathname}${parsed.search}${parsed.hash}`
        }
      }
    } catch {
      return value
    }
    return value
  }
  if (value.startsWith('/media/')) {
    // 站内绝对媒体路径补全 origin。
    return API_ORIGIN ? `${API_ORIGIN}${value}` : value
  }
  if (value.startsWith('media/')) {
    return API_ORIGIN ? `${API_ORIGIN}/${value}` : value
  }
  return value
}

// 深度遍历接口响应，把头像/封面等媒体字段改为可直接访问的地址。
const normalizeMediaUrls = (payload: any): any => {
  if (Array.isArray(payload)) {
    // 数组响应逐项递归处理。
    return payload.map(item => normalizeMediaUrls(item))
  }
  if (!payload || typeof payload !== 'object') {
    return payload
  }

  const next = { ...payload }
  Object.keys(next).forEach(key => {
    const value = next[key]
    if (typeof value === 'string' && (key === 'avatar' || key === 'cover_image' || key === 'author_avatar')) {
      next[key] = toMediaUrl(value)
      return
    }
    next[key] = normalizeMediaUrls(value)
  })

  return next
}

api.interceptors.request.use(
  config => {
    // 自动携带访问令牌。
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
    // 统一做媒体地址标准化，减少页面层处理。
    response.data = normalizeMediaUrls(response.data)
    return response
  },
  async error => {
    // 令牌失效时清理本地登录态并跳转登录页。
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
