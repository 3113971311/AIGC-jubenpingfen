import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 310000, // 评分最长 5 分钟，留余量
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    let msg = '请求失败'
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      msg = detail
    } else if (Array.isArray(detail)) {
      // FastAPI 422 validation errors
      msg = detail.map(d => {
        const field = d.loc?.join('.') || ''
        return `${field}: ${d.msg}`
      }).join('; ')
    } else if (err.message) {
      msg = err.message
    }
    ElMessage.error(msg)
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.hash = '#/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const login = (data) => api.post('/auth/login', data)
export const getMe = () => api.get('/auth/me')

// Scripts
export const uploadScript = (file) => {
  const fd = new FormData()
  fd.append('file', file)
  return api.post('/scripts/upload', fd)
}
export const createTextScript = (title, content) =>
  api.post('/scripts/text', { title, content })
export const listScripts = (params) => api.get('/scripts', { params })
export const getScript = (id) => api.get(`/scripts/${id}`)
export const deleteScript = (id) => api.delete(`/scripts/${id}`)

// Models (user facing)
export const getActiveModels = () => api.get('/models/active')

// Scoring
export const scoreScript = (scriptId, modelConfigId) =>
  api.post(`/scripts/${scriptId}/score`, { model_config_id: modelConfigId })
export const getScore = (id) => api.get(`/scores/${id}`)
export const getScoreProgress = (id) => api.get(`/scores/${id}/progress`)
export const getScoreHistory = (params) => api.get('/scores/history', { params })

// Points
export const getPointsLog = (params) => api.get('/points/log', { params })

// Admin
export const adminListUsers = (params) => api.get('/admin/users', { params })
export const adminCreateUser = (data) => api.post('/admin/users', data)
export const adminUpdateUser = (id, data) => api.put(`/admin/users/${id}`, data)
export const adminDeleteUser = (id) => api.delete(`/admin/users/${id}`)
export const adminToggleUser = (id) => api.put(`/admin/users/${id}/toggle`)
export const adminRechargeUser = (id, amount) => api.post(`/admin/users/${id}/recharge`, { amount })

export const adminListModels = () => api.get('/admin/models')
export const adminCreateModel = (data) => api.post('/admin/models', data)
export const adminUpdateModel = (id, data) => api.put(`/admin/models/${id}`, data)
export const adminDeleteModel = (id) => api.delete(`/admin/models/${id}`)
export const adminToggleModel = (id) => api.put(`/admin/models/${id}/toggle`)
export const adminTestModel = (id) => api.post(`/admin/models/${id}/test`)

export const adminListScores = (params) => api.get('/admin/scores', { params })
export const adminGetStats = () => api.get('/admin/stats')
export const adminGetSettings = () => api.get('/admin/settings')
export const adminUpdateSettings = (data) => api.put('/admin/settings', data)

export default api
