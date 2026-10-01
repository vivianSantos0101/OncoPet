// Textos e regras de exibicao do painel de cuidados paliativos (RF-06).
// Os calculos ficam no backend (app/analytics/palliative.py).

export const LEVELS = {
  critico: { label: 'Crítico', plural: 'Críticos', hint: 'Precisa de ação logo' },
  atencao: { label: 'Atenção', plural: 'Em atenção', hint: 'Acompanhar de perto' },
  estavel: { label: 'Estável', plural: 'Estáveis', hint: 'Sem alertas' },
}
export const LEVEL_ORDER = ['critico', 'atencao', 'estavel']

export const TOLERANCE = {
  boa: { label: 'Boa', level: 'estavel' },
  moderada: { label: 'Moderada', level: 'atencao' },
  ruim: { label: 'Ruim', level: 'critico' },
  sem_dados: { label: 'Sem registro', level: null },
}

export const levelLabel = (level) => LEVELS[level]?.label ?? level
export const toleranceLabel = (t) => TOLERANCE[t]?.label ?? t

/** Pacientes do nivel escolhido (null = todos), mantendo a ordem do backend. */
export function filterByLevel(patients, level) {
  return level ? patients.filter(p => p.level === level) : patients
}

/** "hoje", "ontem", "há 5 dias" ou "nunca". */
export function lastLogText(days) {
  if (days === null || days === undefined) return 'nunca'
  if (days === 0) return 'hoje'
  if (days === 1) return 'ontem'
  return `há ${days} dias`
}

/**
 * Dados do grafico "dor apos a sessao x demais dias": so pacientes que tem
 * os dois valores (sem um deles nao ha o que comparar).
 */
export function postSessionChartData(patients) {
  return patients
    .filter(p => p.pain_after_session !== null && p.pain_other_days !== null)
    .map(p => ({
      name: p.name,
      after: p.pain_after_session,
      other: p.pain_other_days,
      diff: Math.round((p.pain_after_session - p.pain_other_days) * 100) / 100,
    }))
}
