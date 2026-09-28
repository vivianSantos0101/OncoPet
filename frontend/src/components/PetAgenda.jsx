import { useState, useEffect } from 'react'
import api from '../api'

function PetAgenda({ pet, canCreate = false }) {
  const [reminders, setReminders] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    title: '', reminder_type: 'medicacao', date: '', time: '',
    recurrence: 'nenhuma', notes: '',
  })
  const [success, setSuccess] = useState('')

  useEffect(() => { loadReminders() }, [pet.id])

  const loadReminders = async () => {
    try {
      const res = await api.get(`/reminders/pet/${pet.id}`)
      setReminders(res.data)
    } catch (err) { console.error(err) }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await api.post('/reminders/', {
        pet_id: pet.id,
        title: form.title,
        reminder_type: form.reminder_type,
        date: form.date,
        time: form.time || null,
        recurrence: form.recurrence !== 'nenhuma' ? form.recurrence : null,
        notes: form.notes || null,
      })
      setForm({ title: '', reminder_type: 'medicacao', date: '', time: '', recurrence: 'nenhuma', notes: '' })
      setShowForm(false)
      setSuccess('Lembrete criado!'); setTimeout(() => setSuccess(''), 3000)
      loadReminders()
    } catch (err) { console.error(err) }
  }

  const handleComplete = async (id) => {
    await api.patch(`/reminders/${id}`, { is_completed: true })
    loadReminders()
  }

  const upcoming = reminders.filter(r => !r.is_completed)
  const completed = reminders.filter(r => r.is_completed)

  const typeLabels = {
    sessao: 'Sessao', medicacao: 'Medicacao',
    consulta: 'Consulta', exame: 'Exame', outro: 'Outro',
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h4>Agenda - {pet.name}</h4>
        {canCreate && (
          <button className="primary" style={{ padding: '8px 16px', fontSize: 12 }} onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancelar' : 'Novo Lembrete'}
          </button>
        )}
      </div>

      {success && <div className="success-msg">{success}</div>}

      {/* Form - so para vet */}
      {showForm && canCreate && (
        <form onSubmit={handleSubmit} style={{ marginBottom: 20, padding: 20, background: '#f8faf9', borderRadius: 'var(--radius-sm)' }}>
          <div className="grid-2">
            <div>
              <label>Titulo</label>
              <input value={form.title} onChange={e => setForm({...form, title: e.target.value})} placeholder="Ex: Aplicar Doxorrubicina" required />
            </div>
            <div>
              <label>Tipo</label>
              <select value={form.reminder_type} onChange={e => setForm({...form, reminder_type: e.target.value})}>
                <option value="sessao">Sessao</option>
                <option value="medicacao">Medicacao</option>
                <option value="consulta">Consulta</option>
                <option value="exame">Exame</option>
                <option value="outro">Outro</option>
              </select>
            </div>
          </div>
          <div className="grid-3">
            <div>
              <label>Data</label>
              <input type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})} required />
            </div>
            <div>
              <label>Horario</label>
              <input type="time" value={form.time} onChange={e => setForm({...form, time: e.target.value})} />
            </div>
            <div>
              <label>Recorrencia</label>
              <select value={form.recurrence} onChange={e => setForm({...form, recurrence: e.target.value})}>
                <option value="nenhuma">Nenhuma</option>
                <option value="diaria">Diaria</option>
                <option value="semanal">Semanal</option>
                <option value="mensal">Mensal</option>
              </select>
            </div>
          </div>
          <label>Notas</label>
          <textarea value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} rows={2} placeholder="Instrucoes adicionais..." />
          <button type="submit" className="primary" style={{ marginTop: 4 }}>Criar Lembrete</button>
        </form>
      )}

      {/* Lembretes pendentes */}
      {upcoming.length === 0 ? (
        <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Nenhum lembrete pendente.</p>
      ) : (
        upcoming.map(r => (
          <div key={r.id} style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '14px 16px', background: '#fafcfb',
            borderRadius: 'var(--radius-sm)', marginBottom: 10,
            borderLeft: '3px solid var(--mint)',
          }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="badge badge-mint">{typeLabels[r.reminder_type]}</span>
                <strong style={{ fontSize: 14 }}>{r.title}</strong>
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                {new Date(r.date).toLocaleDateString('pt-BR')}
                {r.time && ` as ${r.time}`}
                {r.recurrence && ` (${r.recurrence})`}
              </p>
              {r.notes && <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{r.notes}</p>}
            </div>
            <button
              className="outline"
              style={{ padding: '6px 12px', fontSize: 11 }}
              onClick={() => handleComplete(r.id)}
            >
              Concluir
            </button>
          </div>
        ))
      )}

      {/* Concluidos */}
      {completed.length > 0 && (
        <details style={{ marginTop: 16 }}>
          <summary style={{ cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)', fontWeight: 600 }}>
            {completed.length} concluido(s)
          </summary>
          <div style={{ marginTop: 8 }}>
            {completed.map(r => (
              <div key={r.id} style={{
                padding: '10px 14px', background: '#f5f5f5',
                borderRadius: 'var(--radius-sm)', marginBottom: 6,
                opacity: 0.6, textDecoration: 'line-through',
              }}>
                <span style={{ fontSize: 13 }}>{r.title} - {new Date(r.date).toLocaleDateString('pt-BR')}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}

export default PetAgenda
