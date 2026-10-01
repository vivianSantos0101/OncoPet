import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'

/** Seta + texto: a direcao nunca e so cor. */
function Direction({ value, goodWhenUp, children }) {
  const Icon = value > 0 ? ArrowUpRight : value < 0 ? ArrowDownRight : Minus
  const tone = value === 0 ? 'neutral' : (value > 0) === goodWhenUp ? 'good' : 'bad'
  return <span className={`trend trend-${tone}`}><Icon size={15} aria-hidden="true" />{children}</span>
}

export default Direction
