import { useState, useEffect } from 'react'
import { Bell, Check, X, ChevronDown } from 'lucide-react'
import api from '../api'

const TYPE_LABELS = {
  sessao: 'Sessao',
  medicacao: 'Medicacao',
  consulta: 'Consulta',
  exame: 'Exame',
  outro: 'Lembrete',
}

// No celular comeca recolhido para nao cobrir a tela
const startsOpen = () => typeof window === 'undefined' || !window.matchMedia('(max-width: 640px)').matches

/** Lembretes do dia para o tutor: painel compacto que pode ser recolhido. */
function Notifications() {
  const [reminders, setReminders] = useState([])
  const [dismissed, setDismissed] = useState([])
  const [open, setOpen] = useState(startsOpen)

  useEffect(() => {
    checkReminders()
    // Verifica a cada 5 minutos
    const interval = setInterval(checkReminders, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const checkReminders = async () => {
    try {
      const res = await api.get('/reminders/today')
      setReminders(res.data)
    } catch (err) {
      // falha silenciosa: notificacao nao e critica
    }
  }

  const handleDismiss = (id) => setDismissed(prev => [...prev, id])

  const handleComplete = async (id) => {
    try {
      await api.patch(`/reminders/${id}`, { is_completed: true })
      handleDismiss(id)
    } catch (err) { console.error(err) }
  }

  const visible = reminders.filter(r => !dismissed.includes(r.id))
  if (visible.length === 0) return null

  const count = `${visible.length} ${visible.length === 1 ? 'lembrete' : 'lembretes'}`

  if (!open) {
    return (
      <button className="notif-pill" onClick={() => setOpen(true)} aria-label={`Abrir ${count} de hoje`}>
        <Bell size={16} />
        <span>Hoje · {count}</span>
      </button>
    )
  }

  return (
    <section className="notif-panel" aria-label="Lembretes de hoje">
      <header className="notif-head">
        <span className="notif-title"><Bell size={16} /> Hoje · {count}</span>
        <button className="notif-icon" onClick={() => setOpen(false)} aria-label="Recolher lembretes">
          <ChevronDown size={18} />
        </button>
      </header>
      <ul className="notif-list">
        {visible.map(r => (
          <li key={r.id} className={`notif-item notif-${r.reminder_type}`}>
            <div className="notif-text">
              <span className="notif-type">{TYPE_LABELS[r.reminder_type] || r.reminder_type}{r.time && ` · ${r.time}`}</span>
              <strong>{r.title}</strong>
              {r.notes && <small>{r.notes}</small>}
            </div>
            <div className="notif-actions">
              <button className="notif-icon notif-done" onClick={() => handleComplete(r.id)} aria-label="Marcar como feito" title="Feito">
                <Check size={16} />
              </button>
              <button className="notif-icon" onClick={() => handleDismiss(r.id)} aria-label="Dispensar" title="Dispensar">
                <X size={16} />
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default Notifications
