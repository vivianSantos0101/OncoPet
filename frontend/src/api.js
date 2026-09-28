import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

// Interceptor: adiciona o token JWT em todas as requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('oncopet_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor: redireciona para login se 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('oncopet_token')
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

export default api
