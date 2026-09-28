import { test } from 'node:test'
import assert from 'node:assert/strict'
import { painLevel, symptomLabel } from './diary.js'

test('faixas da escala de dor', () => {
  assert.equal(painLevel(null), null)
  assert.equal(painLevel(0).level, 'none')
  assert.deepEqual([1, 3].map(n => painLevel(n).level), ['mild', 'mild'])
  assert.deepEqual([4, 6].map(n => painLevel(n).level), ['moderate', 'moderate'])
  assert.deepEqual([7, 10].map(n => painLevel(n).level), ['severe', 'severe'])
})

test('rotulo do sintoma', () => {
  assert.equal(symptomLabel('inapetencia'), 'Falta de apetite')
  assert.equal(symptomLabel('desconhecido'), 'desconhecido')
})
