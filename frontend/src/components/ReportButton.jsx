import { useState } from 'react'
import { FileDown, LoaderCircle } from 'lucide-react'
import api from '../api'
import { downloadReport } from '../report'

/** Botao "Relatorio PDF" (RF-07): baixa o relatorio clinico unificado do pet. */
function ReportButton({ petId, onError }) {
  const [busy, setBusy] = useState(false)

  const handleClick = async () => {
    setBusy(true)
    try {
      await downloadReport(api, petId)
    } catch (err) {
      console.error(err)
      onError?.('Não foi possível gerar o relatório. Tente de novo em instantes.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <button type="button" className="outline report-btn" onClick={handleClick} disabled={busy}
      title="Baixar relatório clínico em PDF">
      {busy ? <LoaderCircle size={17} className="spin-icon" aria-hidden="true" /> : <FileDown size={17} aria-hidden="true" />}
      <span className="report-btn-label">{busy ? 'Gerando…' : 'Relatório PDF'}</span>
    </button>
  )
}

export default ReportButton
