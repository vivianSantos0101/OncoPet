import { formatDate } from './dates.js'

// Numeros no formato brasileiro (virgula decimal, sem casas desnecessarias)
export const num = (v, digits = 1) => Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: digits })

// Com sinal: +1,5 / −0,8 (sinal de menos tipografico)
export const signed = (v, digits = 1) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${num(Math.abs(v), digits)}`

export const shortDate = (d) => formatDate(d, { day: '2-digit', month: '2-digit' })
