import { formatDate } from '../dates'
import { painLevel, symptomLabel } from '../diary'

/** Lista do diario do tutor (usada pelo tutor e pelo veterinario). */
function DailyLogList({ records, emptyText = 'Nenhum registro ainda.' }) {
  if (records.length === 0) {
    return <p style={{ color: 'var(--text-secondary)' }}>{emptyText}</p>
  }
  return records.map(r => {
    const pain = painLevel(r.pain_score)
    return (
      <div key={r.id} className="timeline-item">
        <div className="log-head">
          <span className="date">{formatDate(r.date)}</span>
          {pain && <span className={`pain-badge pain-${pain.level}`}>Dor {r.pain_score}/10</span>}
        </div>
        <div className="log-meta">
          {r.weight && <span><strong>Peso:</strong> {r.weight} kg</span>}
          {r.general_status && <span className="badge badge-mint">Estado: {r.general_status}</span>}
          {r.appetite && <span className="badge badge-pink">Apetite: {r.appetite}</span>}
          {r.energy_level && <span className="badge badge-mint">Energia: {r.energy_level}</span>}
        </div>
        {(r.symptoms?.length > 0 || r.other_symptoms) && (
          <div className="log-symptoms">
            {r.symptoms?.map(s => <span key={s} className="chip chip-static">{symptomLabel(s)}</span>)}
            {r.other_symptoms && <span className="log-other">{r.other_symptoms}</span>}
          </div>
        )}
        {r.notes && <p className="log-notes">{r.notes}</p>}
      </div>
    )
  })
}

export default DailyLogList
