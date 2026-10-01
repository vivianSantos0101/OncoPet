import { test } from 'node:test'
import assert from 'node:assert/strict'
import { filterByLevel, lastLogText, levelLabel, postSessionChartData, toleranceLabel } from './palliative.js'

const patients = [
  { name: 'Bela', level: 'critico', pain_after_session: 6, pain_other_days: 5.33 },
  { name: 'Thor', level: 'atencao', pain_after_session: 1.1, pain_other_days: null },
  { name: 'Mia', level: 'estavel', pain_after_session: 2.5, pain_other_days: 2 },
]

test('filtro por nivel mantem a ordem', () => {
  assert.deepEqual(filterByLevel(patients, 'critico').map(p => p.name), ['Bela'])
  assert.equal(filterByLevel(patients, null).length, 3)
})

test('texto do ultimo registro', () => {
  assert.equal(lastLogText(null), 'nunca')
  assert.equal(lastLogText(0), 'hoje')
  assert.equal(lastLogText(1), 'ontem')
  assert.equal(lastLogText(12), 'há 12 dias')
})

test('grafico pos-sessao ignora quem nao tem os dois valores', () => {
  assert.deepEqual(postSessionChartData(patients), [
    { name: 'Bela', after: 6, other: 5.33, diff: 0.67 },
    { name: 'Mia', after: 2.5, other: 2, diff: 0.5 },
  ])
})

test('rotulos', () => {
  assert.equal(levelLabel('atencao'), 'Atenção')
  assert.equal(toleranceLabel('sem_dados'), 'Sem registro')
})
