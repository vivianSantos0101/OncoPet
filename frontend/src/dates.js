// Datas do tipo 'AAAA-MM-DD' (sem hora) vindas da API.
//
// new Date('2026-08-31') interpreta a data como meia-noite UTC; no Brasil
// (UTC-3) isso vira 30/08 as 21h e a tela mostra um dia a menos. Aqui a data
// e sempre montada no fuso local.

/** Converte 'AAAA-MM-DD' em Date no fuso local (sem deslocar o dia). */
export function parseISODate(value) {
  if (!value) return null
  const [year, month, day] = String(value).slice(0, 10).split('-').map(Number)
  return new Date(year, month - 1, day)
}

/** Formata 'AAAA-MM-DD' como dd/mm/aaaa (ou com as opcoes informadas). */
export function formatDate(value, options) {
  const date = parseISODate(value)
  return date ? date.toLocaleDateString('pt-BR', options) : ''
}

/** Data de hoje no fuso local, no formato 'AAAA-MM-DD' (para inputs type=date). */
export function todayISO() {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}
