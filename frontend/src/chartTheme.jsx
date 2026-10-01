// Tema dos graficos (recharts), compartilhado pelas telas de analise.
// Paleta validada (scripts/validate_palette.js do skill de dataviz): passa em
// contraste com o fundo branco e em separacao para daltonismo.
export const COLOR_VALUE = '#0ca678'   // 1a serie (valor medido)
export const COLOR_AVERAGE = '#3b5bdb' // 2a serie (media movel / comparacao)
export const AXIS = { fontSize: 11, tick: { fill: '#94a3aa' }, axisLine: false, tickLine: false }
export const TOOLTIP_STYLE = { borderRadius: 12, border: 'none', boxShadow: '0 8px 24px rgba(16,42,51,.12)', fontSize: 13 }
// Texto da legenda na cor de texto (a cor fica so no traco ao lado)
export const legendText = (value) => <span style={{ color: '#5f7179' }}>{value}</span>
