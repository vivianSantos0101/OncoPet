import { useState, useEffect } from 'react'
import api, { getErrorMessage } from '../api'
import { formatDate, todayISO } from '../dates'

const STATUS_LABEL = { ativo: 'Ativo', concluido: 'Concluido', suspenso: 'Suspenso' }
const STATUS_BADGE = { ativo: 'badge-mint', concluido: 'badge-mint', suspenso: 'badge-pink' }

const emptyForm = () => ({
  name: '', drug_name: '', dose_mg_m2: '', planned_sessions: '',
  interval_days: '', start_date: todayISO(), notes: '',
})

const fmtDate = formatDate

/**
 * Protocolos de quimioterapia do pet (RF-04).
 * canManage=true (vet): cria protocolo e altera status. Tutor so visualiza.
 * onChanged: avisa o pai para recarregar (ex: lista de protocolos da sessao).
 */
function ProtocolPanel({ pet, canManage = false, onChanged }) {
  const [protocols, setProtocols] = useState([])
  const [form, setForm] = useState(emptyForm())
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { load() }, [pet.id])

  const load = async () => {
    try {
      const res = await api.get(`/protocols/pet/${pet.id}`)
      setProtocols(res.data)
    } catch (err) { console.error('Erro ao carregar protocolos:', err) }
  }

  const showError = (err) => {
    setError(getErrorMessage(err, 'Verifique os campos do protocolo'))
  }

  const handleSubmit = async (e) => {
    e.preventDefault(); setError('')
    try {
      await api.post('/protocols/', {
        pet_id: pet.id,
        name: form.name,
        drug_name: form.drug_name || null,
        dose_mg_m2: form.dose_mg_m2 ? parseFloat(form.dose_mg_m2) : null,
        planned_sessions: parseInt(form.planned_sessions),
        interval_days: form.interval_days ? parseInt(form.interval_days) : null,
        start_date: form.start_date,
        notes: form.notes || null,
      })
      setForm(emptyForm()); setShowForm(false)
      load(); onChanged?.()
    } catch (err) { showError(err) }
  }

  const setStatus = async (protocol, status) => {
    setError('')
    try {
      await api.patch(`/protocols/${protocol.id}`, { status })
      load(); onChanged?.()
    } catch (err) { showError(err) }
  }

  return (
    <div>
      {error && <p className="error">{error}</p>}

      {canManage && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4>Protocolos de quimioterapia</h4>
            <button className={showForm ? 'outline' : 'primary'} onClick={() => setShowForm(!showForm)}>
              {showForm ? 'Cancelar' : 'Novo protocolo'}
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleSubmit} style={{ marginTop: 20 }}>
              <div className="grid-2">
                <div><label>Nome do protocolo</label><input value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Ex: CHOP, Doxorrubicina solo" required /></div>
                <div><label>Inicio</label><input type="date" value={form.start_date} onChange={e => setForm({...form, start_date: e.target.value})} required /></div>
              </div>
              <div className="grid-2">
                <div><label>Medicamento</label><input value={form.drug_name} onChange={e => setForm({...form, drug_name: e.target.value})} placeholder="Ex: Doxorrubicina" /></div>
                <div><label>Dose padrao (mg/m2)</label><input type="number" step="0.01" min="0" value={form.dose_mg_m2} onChange={e => setForm({...form, dose_mg_m2: e.target.value})} /></div>
              </div>
              <div className="grid-2">
                <div><label>Sessoes planejadas</label><input type="number" min="1" value={form.planned_sessions} onChange={e => setForm({...form, planned_sessions: e.target.value})} required /></div>
                <div><label>Intervalo entre sessoes (dias)</label><input type="number" min="1" value={form.interval_days} onChange={e => setForm({...form, interval_days: e.target.value})} placeholder="Ex: 21" /></div>
              </div>
              <label>Observacoes</label>
              <textarea value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} rows={2} />
              <button type="submit" className="primary" style={{ width: '100%', marginTop: 8 }}>Criar protocolo</button>
            </form>
          )}
        </div>
      )}

      {protocols.length === 0 ? (
        <div className="card">
          {!canManage && <h4 style={{ marginBottom: 8 }}>Protocolo de tratamento</h4>}
          <p style={{ color: 'var(--text-secondary)' }}>Nenhum protocolo cadastrado.</p>
        </div>
      ) : (
        protocols.map(p => (
          <div key={p.id} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
              <div>
                <h4>{p.name}</h4>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  {p.drug_name || 'Medicamento nao informado'}
                  {p.dose_mg_m2 && ` - ${p.dose_mg_m2} mg/m2`}
                  {p.interval_days && ` - a cada ${p.interval_days} dias`}
                  {` - inicio ${fmtDate(p.start_date)}`}
                </p>
              </div>
              <span className={`badge ${STATUS_BADGE[p.status]}`}>{STATUS_LABEL[p.status]}</span>
            </div>

            <div style={{ margin: '16px 0 6px', display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <strong>{p.executed_sessions} de {p.planned_sessions} sessoes</strong>
              <span>{p.progress_percent}%</span>
            </div>
            <div className="progress-track" role="progressbar" aria-valuenow={p.progress_percent} aria-valuemin={0} aria-valuemax={100}>
              <div className="progress-fill" style={{ width: `${p.progress_percent}%` }} />
            </div>

            <div style={{ marginTop: 12, fontSize: 13, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              {p.last_session_date && <span>Ultima sessao: {fmtDate(p.last_session_date)}</span>}
              {p.next_session_date && (
                <span style={p.is_overdue ? { color: 'var(--pink-dark)', fontWeight: 600 } : undefined}>
                  Proxima prevista: {fmtDate(p.next_session_date)}{p.is_overdue && ' (atrasada)'}
                </span>
              )}
              {p.status === 'ativo' && <span>Restantes: {p.remaining_sessions}</span>}
            </div>
            {p.notes && <p style={{ marginTop: 8, fontSize: 13, color: 'var(--text-secondary)' }}>{p.notes}</p>}

            {canManage && p.status !== 'concluido' && (
              <div style={{ marginTop: 12 }}>
                {p.status === 'ativo'
                  ? <button className="outline" onClick={() => setStatus(p, 'suspenso')} style={{ padding: '6px 12px', fontSize: 12 }}>Suspender</button>
                  : <button className="outline" onClick={() => setStatus(p, 'ativo')} style={{ padding: '6px 12px', fontSize: 12 }}>Retomar</button>}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}

export default ProtocolPanel
