import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { ChevronRight, CircleCheck, OctagonAlert, TriangleAlert, RefreshCw } from 'lucide-react'
import api, { getErrorMessage } from '../api'
import PetAvatar from './PetAvatar'
import DataTable from './DataTable'
import Direction from './Direction'
import { num, signed } from '../format'
import { formatDate } from '../dates'
import { AXIS, COLOR_AVERAGE, COLOR_VALUE, TOOLTIP_STYLE, legendText } from '../chartTheme'
import { LEVELS, LEVEL_ORDER, filterByLevel, lastLogText, postSessionChartData } from '../palliative'

export const LEVEL_ICONS = { critico: OctagonAlert, atencao: TriangleAlert, estavel: CircleCheck }

/** Nivel sempre com icone + texto (nunca so cor). */
export function LevelChip({ level, children }) {
  const Icon = LEVEL_ICONS[level]
  return (
    <span className={`status-chip level-${level}`}>
      <Icon size={14} aria-hidden="true" />{children ?? LEVELS[level].label}
    </span>
  )
}

function Metric({ label, children }) {
  return (
    <div className="pal-metric">
      <span className="pal-metric-label">{label}</span>
      <span className="pal-metric-value">{children}</span>
    </div>
  )
}

function PatientCard({ patient: p, onOpen }) {
  return (
    <article className={`pal-patient level-border-${p.level}`}>
      <button type="button" className="pal-patient-head" onClick={onOpen}
        aria-label={`Abrir prontuário de ${p.name}`}>
        <PetAvatar pet={p} size={48} radius={14} />
        <div className="pal-patient-name">
          <strong>{p.name}</strong>
          <span>{p.cancer_type || p.breed}{p.tutor_name && ` · Tutor: ${p.tutor_name}`}</span>
        </div>
        <LevelChip level={p.level} />
        <ChevronRight size={18} className="pal-open" aria-hidden="true" />
      </button>

      <div className="pal-metrics">
        <Metric label="Dor (últimas 4 semanas)">
          {p.recent_pain_mean !== null ? <>{num(p.recent_pain_mean)}<small>/10</small></> : '—'}
          {p.pain_recent_change !== null && p.pain_recent_change !== 0 && (
            <Direction value={p.pain_recent_change} goodWhenUp={false}>{signed(p.pain_recent_change)}</Direction>
          )}
        </Metric>
        <Metric label="Peso desde o início">
          {p.weight_change_percent !== null ? `${signed(p.weight_change_percent)}%` : '—'}
        </Metric>
        <Metric label="Último registro do tutor">{lastLogText(p.days_since_last_log)}</Metric>
        <Metric label="Sessões feitas">{p.sessions_count}</Metric>
      </div>

      {p.alerts.length > 0 && (
        <ul className="pal-alerts">
          {p.alerts.map(a => {
            const Icon = LEVEL_ICONS[a.level]
            return (
              <li key={a.code + a.message} className={`pal-alert alert-${a.level}`}>
                <Icon size={15} aria-hidden="true" />
                <span><span className="sr-only">{LEVELS[a.level].label}: </span>{a.message}</span>
              </li>
            )
          })}
        </ul>
      )}
    </article>
  )
}

function PostSessionChart({ patients }) {
  const data = postSessionChartData(patients)
  const missing = patients.length - data.length
  if (data.length === 0) return null
  return (
    <div className="card">
      <div className="chart-head">
        <div>
          <h4>Dor logo após as sessões × demais dias</h4>
          <span className="insight-sub">Média da escala de dor (0 a 10) no diário do tutor, do 1º ao 3º dia depois de cada sessão</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={70 + data.length * 52}>
        <BarChart data={data} layout="vertical" barGap={2} barCategoryGap="28%"
          margin={{ top: 4, right: 16, left: 4, bottom: 0 }}>
          <CartesianGrid stroke="#e6eef0" horizontal={false} />
          <XAxis type="number" domain={[0, 10]} ticks={[0, 2, 4, 6, 8, 10]} {...AXIS} />
          <YAxis type="category" dataKey="name" width={64} {...AXIS} tick={{ fill: '#5f7179', fontSize: 12 }} />
          <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'rgba(16,42,51,.04)' }}
            formatter={(v, name) => [`${num(v, 2)}/10`, name]} />
          <Legend iconType="square" wrapperStyle={{ fontSize: 12 }} formatter={legendText} />
          <Bar dataKey="other" name="Demais dias" fill={COLOR_VALUE} radius={[0, 4, 4, 0]} maxBarSize={14} />
          <Bar dataKey="after" name="1 a 3 dias após a sessão" fill={COLOR_AVERAGE} radius={[0, 4, 4, 0]} maxBarSize={14} />
        </BarChart>
      </ResponsiveContainer>
      {missing > 0 && (
        <p className="insight-sub" style={{ marginTop: 6 }}>
          {missing === 1 ? '1 paciente não aparece' : `${missing} pacientes não aparecem`}: todos os registros do diário caíram logo após uma sessão, então não há dias para comparar.
        </p>
      )}
      <DataTable
        columns={[
          { key: 'name', label: 'Paciente' },
          { key: 'other', label: 'Demais dias', format: v => num(v, 2) },
          { key: 'after', label: 'Após a sessão', format: v => num(v, 2) },
          { key: 'diff', label: 'Diferença', format: v => signed(v, 2) },
        ]}
        rows={data}
      />
    </div>
  )
}

/** Painel de cuidados paliativos (RF-06): pacientes do vet, dos mais criticos aos estaveis. */
function PalliativeDashboard({ onOpenPet }) {
  const [data, setData] = useState(null)
  const [filter, setFilter] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true); setError('')
    try {
      setData((await api.get('/palliative/overview')).data)
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível carregar o painel'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (error) return <p className="error">{error}</p>
  if (!data) return <div className="card empty-state"><p>Carregando painel…</p></div>

  const patients = filterByLevel(data.patients, filter)

  return (
    <section className="palliative" aria-label="Cuidados paliativos">
      <div className="pal-intro">
        <div>
          <h3>Cuidados paliativos</h3>
          <p className="insight-sub">
            Cruza o diário do tutor com as sessões de quimioterapia para mostrar quem precisa de atenção.
            Referência: {formatDate(data.reference_date)}.
          </p>
        </div>
        <button type="button" className="outline icon-btn" onClick={load} disabled={loading} title="Atualizar">
          <RefreshCw size={18} className={loading ? "spin-icon" : ""} aria-hidden="true" />
          <span className="sr-only">Atualizar</span>
        </button>
      </div>

      <div className="level-tiles" role="group" aria-label="Filtrar por nível">
        {LEVEL_ORDER.map(level => {
          const Icon = LEVEL_ICONS[level]
          const active = filter === level
          return (
            <button key={level} type="button" aria-pressed={active}
              className={`level-tile tile-${level} ${active ? 'active' : ''}`}
              onClick={() => setFilter(active ? null : level)}>
              <Icon size={20} aria-hidden="true" />
              <strong>{data[level]}</strong>
              <span className="level-tile-label">{LEVELS[level].plural}</span>
              <span className="level-tile-hint">{LEVELS[level].hint}</span>
            </button>
          )
        })}
      </div>

      {filter && (
        <p className="pal-filter-note">
          Mostrando só pacientes <strong>{LEVELS[filter].plural.toLowerCase()}</strong>.{' '}
          <button type="button" className="link-btn" onClick={() => setFilter(null)}>Ver todos</button>
        </p>
      )}

      {data.patients.length === 0 ? (
        <div className="card empty-state"><h3>Nenhum paciente</h3><p>Os pacientes atribuídos a você aparecem aqui.</p></div>
      ) : patients.length === 0 ? (
        <div className="card empty-state"><p>Nenhum paciente neste nível.</p></div>
      ) : (
        <div className="pal-list">
          {patients.map(p => <PatientCard key={p.pet_id} patient={p} onOpen={() => onOpenPet(p.pet_id)} />)}
        </div>
      )}

      <PostSessionChart patients={data.patients} />
    </section>
  )
}

export default PalliativeDashboard
