import { useState, useEffect } from 'react'
import api from '../api'

function Notifications() {
  const [reminders, setReminders] = useState([])
  const [showPopup, setShowPopup] = useState(false)
  const [dismissed, setDismissed] = useState([])

  useEffect(() => {
    checkReminders()
    // Verifica a cada 5 minutos
    const interval = setInterval(checkReminders, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const checkReminders = async () => {
    try {
      const res = await api.get('/reminders/today')
      const active = res.data.filter(r => !dismissed.includes(r.id))
      setReminders(active)
      if (active.length > 0) {
        setShowPopup(true)
      }
    } catch (err) {
      // silently fail
    }
  }

  const handleDismiss = (id) => {
    setDismissed([...dismissed, id])
    setReminders(reminders.filter(r => r.id !== id))
    if (reminders.length <= 1) setShowPopup(false)
  }

  const handleComplete = async (id) => {
    try {
      await api.patch(`/reminders/${id}`, { is_completed: true })
      handleDismiss(id)
    } catch (err) { console.error(err) }
  }

  if (!showPopup || reminders.length === 0) return null

  const typeLabels = {
    sessao: 'Sessao',
    medicacao: 'Medicacao',
    consulta: 'Consulta',
    exame: 'Exame',
    outro: 'Lembrete',
  }

  const typeColors = {
    sessao: 'var(--pink)',
    medicacao: 'var(--mint)',
    consulta: '#74b9ff',
    exame: '#fdcb6e',
    outro: '#a29bfe',
  }

  return (
    <div style={{
      position: 'fixed', top: 20, right: 20, zIndex: 9999,
      maxWidth: 380, width: '100%',
    }}>
      {reminders.map(r => (
        <div key={r.id} style={{
          background: 'white',
          borderRadius: 'var(--radius)',
          padding: '18px 20px',
          marginBottom: 12,
          boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
          borderLeft: `4px solid ${typeColors[r.reminder_type] || 'var(--mint)'}`,
          animation: 'slideIn 0.3s ease',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span style={{
                fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
                color: typeColors[r.reminder_type] || 'var(--mint-dark)',
                letterSpacing: '0.5px',
              }}>
                {typeLabels[r.reminder_type] || r.reminder_type}
              </span>
              <p style={{ fontWeight: 700, fontSize: 15, marginTop: 4 }}>{r.title}</p>
              {r.time && <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>Horario: {r.time}</p>}
              {r.notes && <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{r.notes}</p>}
            </div>
            <button
              onClick={() => handleDismiss(r.id)}
              style={{ background: 'none', padding: 4, fontSize: 18, color: '#999', lineHeight: 1 }}
            >
              x
            </button>
          </div>
          <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <button className="primary" style={{ padding: '6px 14px', fontSize: 12 }} onClick={() => handleComplete(r.id)}>
              Concluido
            </button>
            <button className="outline" style={{ padding: '6px 14px', fontSize: 12 }} onClick={() => handleDismiss(r.id)}>
              Dispensar
            </button>
          </div>
        </div>
      ))}

      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>
  )
}

export default Notifications
