import { test } from 'node:test'
import assert from 'node:assert/strict'
import { filenameFromDisposition } from './report.js'

test('nome do arquivo do relatorio', () => {
  assert.equal(filenameFromDisposition('attachment; filename="relatorio-luna-2026-09-30.pdf"'), 'relatorio-luna-2026-09-30.pdf')
  assert.equal(filenameFromDisposition("attachment; filename*=UTF-8''relat%C3%B3rio.pdf"), 'relatório.pdf')
  assert.equal(filenameFromDisposition(undefined), null)
})
