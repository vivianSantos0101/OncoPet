/** Tabela com os mesmos dados do grafico (acessibilidade: nao depender so da imagem). */
function DataTable({ columns, rows, summary = 'Ver dados em tabela' }) {
  return (
    <details className="chart-table">
      <summary>{summary}</summary>
      <table>
        <thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => <tr key={i}>{columns.map(c => <td key={c.key}>{c.format ? c.format(r[c.key]) : r[c.key]}</td>)}</tr>)}
        </tbody>
      </table>
    </details>
  )
}

export default DataTable
