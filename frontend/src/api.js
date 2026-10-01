import axios from 'axios'

// A sessao fica num cookie HttpOnly criado pelo backend no login: o navegador
// envia sozinho e o JavaScript nao tem acesso ao token (nada no localStorage).
const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  // Protecao contra CSRF: o backend recusa alteracoes feitas so com o cookie,
  // sem este cabecalho (que outro site nao consegue enviar)
  headers: { 'X-Requested-With': 'XMLHttpRequest' },
})

// Evento disparado quando a sessao expira; o App volta para a tela de login
export const SESSION_EXPIRED = 'oncopet:session-expired'

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || ''
    if (error.response?.status === 401 && !url.startsWith('/auth/')) {
      window.dispatchEvent(new Event(SESSION_EXPIRED))
    }
    return Promise.reject(error)
  }
)

// Nomes amigaveis dos campos para mensagens de validacao (erro 422)
const FIELD_LABELS = {
  weight: 'Peso', weight_at_session: 'Peso no dia', age_years: 'Idade (anos)',
  age_months: 'Idade (meses)', dose_mg_m2: 'Dose (mg/m2)',
  planned_sessions: 'Sessoes planejadas', interval_days: 'Intervalo entre sessoes',
  pain_score: 'Escala de dor',
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
