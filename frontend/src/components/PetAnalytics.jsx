import { useState } from 'react'
import {
  ComposedChart, LineChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'
import { AlertTriangle, ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import { formatDate } from '../dates'
import { symptomLabel } from '../diary'

// Paleta validada (scripts/validate_palette.js do skill de dataviz): passa em
// contraste com o fundo branco e em separacao para daltonismo.
const COLOR_VALUE = '#0ca678'   // valor medido
const COLOR_AVERAGE = '#3b5bdb' // media movel
const AXIS = { fontSize: 11, tick: { fill: '#94a3aa' }, axisLine: false, tickLine: false }
const TOOLTIP_STYLE = { borderRadius: 12, border: 'none', boxShadow: '0 8px 24px rgba(16,42,51,.12)', fontSize: 13 }
// Texto da legenda na cor de texto (a cor fica so no traco ao lado)
const legendText = (value) => <span style={{ color: '#5f7179' }}>{value}</span>
const MANY_POINTS = 12  // acima disso os pontos ficam so no hover, para nao poluir

const num = (v, digits = 1) => Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: digits })
const signed = (v, digits = 1) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${num(Math.abs(v), digits)}`
const shortDate = (d) => formatDate(d, { day: '2-digit', month: '2-digit' })

/** Seta + texto: a direcao nunca e so cor. */
function Direction({ value, goodWhenUp, children }) {
  const Icon = value > 0 ? ArrowUpRight : value < 0 ? ArrowDownRight : Minus
  const tone = value === 0 ? 'neutral' : (value > 0) === goodWhenUp ? 'good' : 'bad'
  return <span className={`trend trend-${tone}`}><Icon size={15} aria-hidden="true" />{children}</span>
}

function DataTable({ columns, rows }) {
  return (
    <details className="chart-table">
      <summary>Ver dados em tabela</summary>
      <table>
        <thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => <tr key={i}>{columns.map(c => <td key={c.key}>{c.format ? c.format(r[c.key]) : r[c.key]}</td>)}</tr>)}
        </tbody>
      </table>
    </details>
  )
}

/** Estatisticas do tratamento (RF-05), calculadas no backend com NumPy. */
function PetAnalytics({ data }) {
  const [showAverage, setShowAverage] = useState(true)
  if (!data) return null
  const { weight, pain, symptoms, weight_points: weightPoints, pain_points: painPoints } = data
  const topSymptom = symptoms[0]

  const weightData = weightPoints.map(p => ({ ...p, label: shortDate(p.date) }))
  const painData = painPoints.map(p => ({ ...p, label: shortDate(p.date) }))

  return (
    <section className="analytics" aria-label="Analise do tratamento">
      <h4 className="section-title">Analise do tratamento</h4>

      <div className="grid-3 insight-row">
        <div className="insight-card">
          <span className="insight-label">Peso desde o inicio</span>
          {weight ? (
            <>
              <strong className="insight-value">{signed(weight.change_kg)} kg</strong>
              <Direction value={weight.change_kg} goodWhenUp>
                {signed(weight.change_percent)}%{weight.trend_kg_per_week !== null && ` · ${signed(weight.trend_kg_per_week, 2)} kg/semana`}
              </Direction>
              {weight.relevant_loss && (
                <span className="status-chip status-warning"><AlertTriangle size={14} aria-hidden="true" /> Perda de peso relevante (5% ou mais)</span>
              )}
            </>
          ) : <span className="insight-empty">Sem registros de peso</span>}
        </div>

        <div className="insight-card">
          <span className="insight-label">Dor nas ultimas 4 semanas</span>
          {pain && pain.recent_mean !== null ? (
            <>
              <strong className="insight-value">{num(pain.recent_mean)} <small>/10</small></strong>
              {pain.recent_change !== null
                ? <Direction value={pain.recent_change} goodWhenUp={false}>{signed(pain.recent_change)} vs. 4 semanas anteriores</Direction>
                : <span className="insight-sub">Sem periodo anterior para comparar</span>}
              <span className="insight-sub">{num(pain.severe_percent)}% dos registros com dor intensa</span>
            </>
          ) : <span className="insight-empty">Dor nao avaliada no periodo</span>}
        </div>

        <div className="insight-card">
          <span className="insight-label">Sintoma mais frequente</span>
          {topSymptom ? (
            <>
              <strong className="insight-value insight-text">{symptomLabel(topSymptom.symptom)}</strong>
              <span className="insight-sub">em {num(topSymptom.percent)}% dos {data.logs_count} registros</span>
            </>
          ) : <span className="insight-empty">Nenhum sintoma registrado</span>}
        </div>
      </div>

      {painData.length > 1 && (
        <div className="card">
          <div className="chart-head">
            <div>
              <h4>Escala de dor</h4>
              <span className="insight-sub">Linha tracejada laranja: dor intensa (7 ou mais)</span>
            </div>
            <label className="chart-toggle">
              <input type="checkbox" checked={showAverage} onChange={e => setShowAverage(e.target.checked)} />
              Media movel
            </label>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={painData} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
              <CartesianGrid stroke="#e6eef0" vertical={false} />
              <XAxis dataKey="label" {...AXIS} />
              <YAxis domain={[0, 10]} ticks={[0, 2, 4, 6, 8, 10]} {...AXIS} />
              <ReferenceLine y={7} stroke="#e8590c" strokeDasharray="4 4" />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, name) => [name === 'Dor' ? `${v}/10` : num(v), name]} />
              <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} formatter={legendText} />
              <Line type="monotone" dataKey="pain" name="Dor" stroke={COLOR_VALUE} strokeWidth={2}
                dot={painData.length > MANY_POINTS ? false : { r: 4, fill: COLOR_VALUE, stroke: '#fff', strokeWidth: 2 }} activeDot={{ r: 6 }} />
              {showAverage && (
                <Line type="monotone" dataKey="moving_average" name="Media movel (3 registros)" stroke={COLOR_AVERAGE} strokeWidth={2} dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
          <DataTable
            columns={[
              { key: 'date', label: 'Data', format: formatDate },
              { key: 'pain', label: 'Dor (0-10)' },
              { key: 'moving_average', label: 'Media movel', format: v => num(v) },
            ]}
            rows={painPoints}
          />
        </div>
      )}

      {weightData.length > 1 && (
        <div className="card">
          <div className="chart-head">
            <h4>Evolucao de peso (kg)</h4>
            {weight?.trend_kg_per_week !== null && weight && (
              <span className="insight-sub">Tendencia: {signed(weight.trend_kg_per_week, 2)} kg/semana</span>
            )}
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <ComposedChart data={weightData} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
              <defs>
                <linearGradient id="pesoFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={COLOR_VALUE} stopOpacity={0.22} />
                  <stop offset="100%" stopColor={COLOR_VALUE} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#e6eef0" vertical={false} />
              <XAxis dataKey="label" {...AXIS} />
              <YAxis domain={['auto', 'auto']} {...AXIS} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, name) => [`${num(v, 2)} kg`, name]} />
              <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} formatter={legendText} />
              <Area type="monotone" dataKey="weight" name="Peso" stroke={COLOR_VALUE} strokeWidth={2} fill="url(#pesoFill)"
                dot={weightData.length > MANY_POINTS ? false : { r: 4, fill: COLOR_VALUE, stroke: '#fff', strokeWidth: 2 }} activeDot={{ r: 6 }} />
              <Line type="monotone" dataKey="moving_average" name="Media movel (3 registros)" stroke={COLOR_AVERAGE} strokeWidth={2} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
          <DataTable
            columns={[
              { key: 'date', label: 'Data', format: formatDate },
              { key: 'weight', label: 'Peso (kg)', format: v => num(v, 2) },
              { key: 'moving_average', label: 'Media movel', format: v => num(v, 2) },
            ]}
            rows={weightPoints}
          />
        </div>
      )}

      {symptoms.length > 0 && (
        <div className="card">
          <h4 style={{ marginBottom: 14 }}>Frequencia de sintomas</h4>
          <ul className="bar-list">
            {symptoms.map(s => (
              <li key={s.symptom} title={`${symptomLabel(s.symptom)}: ${s.count} vezes (${num(s.percent)}% dos registros)`}>
                <span className="bar-label">{symptomLabel(s.symptom)}</span>
                <span className="bar-track"><span className="bar-fill" style={{ width: `${Math.max(s.percent, 2)}%`, background: COLOR_VALUE }} /></span>
                <span className="bar-value">{s.count}× · {num(s.percent)}%</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

export default PetAnalytics
