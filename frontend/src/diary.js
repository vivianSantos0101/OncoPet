// Sintomas que o tutor pode marcar (mesmas chaves aceitas pela API)
export const SYMPTOMS = [
  { key: 'vomito', label: 'Vomito' },
  { key: 'diarreia', label: 'Diarreia' },
  { key: 'letargia', label: 'Letargia' },
  { key: 'inapetencia', label: 'Falta de apetite' },
  { key: 'febre', label: 'Febre' },
  { key: 'tosse', label: 'Tosse' },
  { key: 'dispneia', label: 'Falta de ar' },
  { key: 'lesao_pele', label: 'Lesao de pele' },
]

export const symptomLabel = (key) => SYMPTOMS.find(s => s.key === key)?.label || key

/** Faixa da escala de dor 0-10. */
export function painLevel(score) {
  if (score === null || score === undefined) return null
  if (score === 0) return { label: 'Sem dor', level: 'none' }
  if (score <= 3) return { label: 'Dor leve', level: 'mild' }
  if (score <= 6) return { label: 'Dor moderada', level: 'moderate' }
  return { label: 'Dor intensa', level: 'severe' }
}
