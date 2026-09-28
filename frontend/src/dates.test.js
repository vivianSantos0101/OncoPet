// Rode com: npm test  (usa o test runner nativo do Node, fuso de Brasilia)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { parseISODate, formatDate, todayISO } from './dates.js'

test('formatDate nao volta um dia no fuso do Brasil', () => {
  assert.equal(formatDate('2026-08-31'), '31/08/2026')
  assert.equal(formatDate('2026-01-01'), '01/01/2026')
})

test('formatDate aceita opcoes e valor vazio', () => {
  assert.equal(formatDate('2026-06-07', { day: '2-digit', month: '2-digit' }), '07/06')
  assert.equal(formatDate(null), '')
})

test('parseISODate ignora a parte de hora', () => {
  assert.equal(parseISODate('2026-09-28T10:00:00').getDate(), 28)
})

test('todayISO usa o dia local mesmo depois das 21h', (t) => {
  // 22h30 de 28/09 em Brasilia = 01h30 UTC de 29/09
  t.mock.timers.enable({ apis: ['Date'], now: new Date('2026-09-29T01:30:00Z') })
  assert.equal(todayISO(), '2026-09-28')
})
