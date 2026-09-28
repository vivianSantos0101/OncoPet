import { painLevel } from '../diary'

/** Escala de dor 0-10 (value null = nao avaliada). Tocar de novo limpa. */
function PainScale({ value, onChange }) {
  const info = painLevel(value)
  return (
    <div className="pain-scale">
      <div className="pain-buttons" role="radiogroup" aria-label="Escala de dor de 0 a 10">
        {Array.from({ length: 11 }, (_, n) => {
          const level = painLevel(n).level
          return (
            <button
              key={n} type="button" role="radio" aria-checked={value === n}
              className={`pain-btn pain-${level} ${value === n ? 'on' : ''}`}
              onClick={() => onChange(value === n ? null : n)}
            >
              {n}
            </button>
          )
        })}
      </div>
      <div className="pain-legend">
        <span>0 · sem dor</span>
        <strong className={info ? `pain-text-${info.level}` : ''}>
          {info ? `${value} · ${info.label}` : 'Toque para avaliar'}
        </strong>
        <span>10 · pior dor</span>
      </div>
    </div>
  )
}

export default PainScale
