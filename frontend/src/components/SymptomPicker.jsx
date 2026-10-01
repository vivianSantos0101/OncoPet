import { Check } from 'lucide-react'
import { SYMPTOMS } from '../diary'

/** Chips para marcar sintomas (value: lista de chaves). */
function SymptomPicker({ value, onChange }) {
  const toggle = (key) => {
    onChange(value.includes(key) ? value.filter(k => k !== key) : [...value, key])
  }
  return (
    <div className="chip-group" role="group" aria-label="Sintomas">
      {SYMPTOMS.map(s => {
        const on = value.includes(s.key)
        return (
          <button key={s.key} type="button" className={`chip ${on ? 'on' : ''}`} aria-pressed={on} onClick={() => toggle(s.key)}>
            {on && <Check size={14} />}{s.label}
          </button>
        )
      })}
    </div>
  )
}

export default SymptomPicker
