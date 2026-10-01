import { useState } from 'react'
import {
  ComposedChart, LineChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'
import { AlertTriangle } from 'lucide-react'
import { formatDate } from '../dates'
import { num, signed, shortDate } from '../format'
import DataTable from './DataTable'
import Direction from './Direction'
import { AXIS, COLOR_AVERAGE, COLOR_VALUE, TOOLTIP_STYLE, legendText } from '../chartTheme'
import { symptomLabel } from '../diary'

const MANY_POINTS = 12  // acima disso os pontos ficam so no hover, para nao poluir

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
