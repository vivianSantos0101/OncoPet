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

// Nomes amigaveis dos campos para mensagens de validacao (erro 422)
const FIELD_LABELS = {
  weight: 'Peso', weight_at_session: 'Peso no dia', age_years: 'Idade (anos)',
  age_months: 'Idade (meses)', dose_mg_m2: 'Dose (mg/m2)',
  planned_sessions: 'Sessoes planejadas', interval_days: 'Intervalo entre sessoes',
}

function describeValidation(item) {
  const field = item.loc?.[item.loc.length - 1]
  const label = FIELD_LABELS[field] || field
  const ctx = item.ctx || {}
  if ('ge' in ctx) return `${label} deve ser maior ou igual a ${ctx.ge}`
  if ('gt' in ctx) return `${label} deve ser maior que ${ctx.gt}`
  if ('le' in ctx) return `${label} deve ser no maximo ${ctx.le}`
  if ('lt' in ctx) return `${label} deve ser menor que ${ctx.lt}`
  return `${label}: valor invalido`
}

// Converte o erro da API em uma mensagem de texto para exibir na tela
export function getErrorMessage(err, fallback = 'Erro') {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) return detail.map(describeValidation).join('. ')
  return fallback
}

export default api
