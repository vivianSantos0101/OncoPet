// Download do relatorio clinico em PDF (RF-07)

/** Nome do arquivo vindo do cabecalho Content-Disposition (ou null). */
export function filenameFromDisposition(header) {
  if (!header) return null
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(header)
  return match ? decodeURIComponent(match[1]) : null
}

/** Busca o PDF com o token (axios) e dispara o download no navegador. */
export async function downloadReport(api, petId) {
  const res = await api.get(`/reports/pet/${petId}`, { responseType: 'blob' })
  const name = filenameFromDisposition(res.headers['content-disposition']) || `relatorio-${petId}.pdf`
  const url = URL.createObjectURL(res.data)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
  return name
}
