import { formatDate } from '../dates'
import { num, signed } from '../format'
import { symptomLabel } from '../diary'
import { TOLERANCE, toleranceLabel } from '../palliative'
import { LEVEL_ICONS, LevelChip } from './PalliativeDashboard'
import { CircleDashed } from 'lucide-react'

function ToleranceChip({ value }) {
  const level = TOLERANCE[value]?.level
  if (!level) {
    return <span className="status-chip level-none"><CircleDashed size={14} aria-hidden="true" />{toleranceLabel(value)}</span>
  }
  return <LevelChip level={level}>{toleranceLabel(value)}</LevelChip>
}

function Compare({ label, after, other, unit, digits = 1 }) {
  return (
    <div className="insight-card">
      <span className="insight-label">{label}</span>
      {after !== null ? (
        <>
          <strong className="insight-value">{num(after, digits)}<small>{unit}</small></strong>
          <span className="insight-sub">
            {other !== null
              ? <>demais dias: {num(other, digits)}{unit} ({signed(after - other, digits)})</>
              : 'sem registros fora do período pós-sessão para comparar'}
          </span>
        </>
      ) : <span className="insight-empty">Sem registros do tutor logo após as sessões</span>}
    </div>
  )
}

/** Alertas do paciente e tolerancia a cada sessao (RF-06), no prontuario. */
function SessionTolerance({ data }) {
  if (!data || (data.sessions.length === 0 && data.alerts.length === 0)) return null
  const { effect } = data

  return (
    <section className="analytics" aria-label="Cuidados paliativos">
      <div className="chart-head" style={{ marginBottom: 10 }}>
        <h4 className="section-title" style={{ margin: 0 }}>Cuidados paliativos</h4>
        <LevelChip level={data.level} />
      </div>

      {data.alerts.length > 0 && (
        <ul className="pal-alerts" style={{ margin: '0 0 16px' }}>
          {data.alerts.map(a => {
            const Icon = LEVEL_ICONS[a.level]
            return (
              <li key={a.code + a.message} className={`pal-alert alert-${a.level}`}>
                <Icon size={15} aria-hidden="true" /><span>{a.message}</span>
              </li>
            )
          })}
        </ul>
      )}

      {effect && (
        <div className="tolerance-compare">
          <Compare label={`Dor do 1º ao ${effect.window_days}º dia após as sessões`}
            after={effect.after_session.pain_mean} other={effect.other_days.pain_mean} unit="/10" />
          <Compare label="Registros com sintomas após as sessões"
            after={effect.after_session.symptom_percent} other={effect.other_days.symptom_percent} unit="%" />
        </div>
      )}

      {data.sessions.length > 0 && (
        <div className="card">
          <h4 style={{ marginBottom: 4 }}>Tolerância a cada sessão</h4>
          <p className="insight-sub" style={{ marginBottom: 8 }}>
            Pelo diário do tutor nos {effect?.window_days ?? 3} dias seguintes. Ruim: dor 7 ou mais, febre ou falta de ar.
          </p>
          <ul className="tolerance-list">
            {[...data.sessions].reverse().map(s => (
              <li key={s.date}>
                <span className="tolerance-date">{formatDate(s.date)}</span>
                <span className="tolerance-detail">
                  {s.drug_name && <strong>{s.drug_name}</strong>}
                  {s.logs === 0 ? (s.drug_name ? ' · ' : '') + 'tutor não registrou nesses dias' : (
                    <>
                      {s.drug_name && ' · '}
                      {s.max_pain !== null ? `dor até ${s.max_pain}/10` : 'dor não avaliada'}
                      {s.symptoms.length > 0 ? ` · ${s.symptoms.map(symptomLabel).join(', ')}` : ' · sem sintomas'}
                    </>
                  )}
                </span>
                <ToleranceChip value={s.tolerance} />
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

export default SessionTolerance
