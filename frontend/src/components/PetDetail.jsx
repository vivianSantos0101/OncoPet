import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '../api'
import PetAgenda from './PetAgenda'
import FileUpload from './FileUpload'
import ProtocolPanel from './ProtocolPanel'

function PetDetail({ pet, onUpdated }) {
  const [sessions, setSessions] = useState([])
  const [records, setRecords] = useState([])
  const [documents, setDocuments] = useState([])
  const [chartData, setChartData] = useState(null)
  const [protocols, setProtocols] = useState([])
  const [subTab, setSubTab] = useState('dashboard')

  // Session form
  const [sessionForm, setSessionForm] = useState({
    date: new Date().toISOString().split('T')[0],
    protocol_id: '', session_type: 'quimioterapia', drug_name: '',
    dose_mg_m2: '', weight_at_session: String(pet.weight), notes: '',
  })
  // Document form
  const [docForm, setDocForm] = useState({
    title: '', doc_type: 'exame_sangue', file_url: '', date: '', notes: '',
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => { loadAll() }, [pet.id])

  const loadAll = async () => {
    try {
      const [s, r, d, c, p] = await Promise.all([
        api.get(`/sessions/pet/${pet.id}`),
        api.get(`/records/pet/${pet.id}`),
        api.get(`/documents/pet/${pet.id}`),
        api.get(`/pets/${pet.id}/chart`),
        api.get(`/protocols/pet/${pet.id}`),
      ])
      setSessions(s.data); setRecords(r.data); setDocuments(d.data); setChartData(c.data); setProtocols(p.data)
    } catch (err) { console.error('Erro ao carregar dados:', err) }
  }

  const handleSessionSubmit = async (e) => {
    e.preventDefault(); setError('')
    try {
      await api.post('/sessions/', {
        pet_id: pet.id,
        protocol_id: sessionForm.protocol_id ? parseInt(sessionForm.protocol_id) : null,
        date: sessionForm.date,
        session_type: sessionForm.session_type,
        drug_name: sessionForm.drug_name || null,
        dose_mg_m2: sessionForm.dose_mg_m2 ? parseFloat(sessionForm.dose_mg_m2) : null,
        weight_at_session: parseFloat(sessionForm.weight_at_session),
        notes: sessionForm.notes || null,
      })
      setSuccess('Sessao registrada!'); setTimeout(() => setSuccess(''), 3000)
      setSessionForm({ ...sessionForm, protocol_id: '', drug_name: '', dose_mg_m2: '', notes: '' })
      loadAll(); onUpdated()
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail) || 'Erro')
    }
  }

  // Ao escolher um protocolo, pre-preenche medicamento e dose (vet pode ajustar)
  const handleProtocolSelect = (protocolId) => {
    const protocol = protocols.find(p => String(p.id) === protocolId)
    setSessionForm({
      ...sessionForm,
      protocol_id: protocolId,
      session_type: protocol ? 'quimioterapia' : sessionForm.session_type,
      drug_name: protocol?.drug_name || sessionForm.drug_name,
      dose_mg_m2: protocol?.dose_mg_m2 ? String(protocol.dose_mg_m2) : sessionForm.dose_mg_m2,
    })
  }

  const activeProtocols = protocols.filter(p => p.status === 'ativo')

  const handleDocSubmit = async (e) => {
    e.preventDefault(); setError('')
    if (!docForm.file_url) {
      setError('Faca o upload do arquivo primeiro')
      return
    }
    try {
      await api.post('/documents/', {
        pet_id: pet.id, title: docForm.title, doc_type: docForm.doc_type,
        file_url: docForm.file_url,
        date: docForm.date ? docForm.date : null,
        notes: docForm.notes || null,
      })
      setSuccess('Documento anexado!'); setTimeout(() => setSuccess(''), 3000)
      setDocForm({ title: '', doc_type: 'exame_sangue', file_url: '', date: '', notes: '' })
      loadAll()
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail) || 'Erro ao salvar')
    }
  }

  const weightChartData = chartData?.weight_history?.map(p => ({
    date: new Date(p.date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
    peso: p.weight,
  })) || []

  return (
    <div>
      {/* Pet header */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        <div className="pet-avatar" style={{ width: 64, height: 64, fontSize: 18 }}>
          {pet.species.includes('gato') ? 'G' : 'C'}
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: 22 }}>{pet.name}</h2>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            {pet.breed} - {pet.weight}kg - SC: {pet.body_surface_area} m2
          </p>
          <div style={{ marginTop: 6, display: 'flex', gap: 8 }}>
            {pet.cancer_type && <span className="badge badge-pink">{pet.cancer_type}</span>}
            {pet.treatment_start_date && <span className="badge badge-mint">Inicio: {new Date(pet.treatment_start_date).toLocaleDateString('pt-BR')}</span>}
          </div>
        </div>
      </div>

      {/* Sub tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
        {['dashboard', 'protocolos', 'sessao', 'registros', 'documentos', 'agenda'].map(t => (
          <button key={t} className={subTab === t ? 'primary' : 'outline'} onClick={() => setSubTab(t)} style={{ textTransform: 'capitalize' }}>
            {t}
          </button>
        ))}
      </div>

      {error && <p className="error">{error}</p>}
      {success && <div className="success-msg">{success}</div>}

      {/* Dashboard com graficos */}
      {subTab === 'dashboard' && (
        <div>
          {/* Stats */}
          {chartData && (
            <div className="grid-4" style={{ marginBottom: 20 }}>
              <div className="stat-card">
                <div className="stat-value">{chartData.sessions_count}</div>
                <div className="stat-label">Sessoes</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{chartData.records_count}</div>
                <div className="stat-label">Registros do Tutor</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{chartData.last_weight || '-'}kg</div>
                <div className="stat-label">Ultimo Peso</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{chartData.treatment_days || '-'}</div>
                <div className="stat-label">Dias de Tratamento</div>
              </div>
            </div>
          )}

          {/* Grafico de peso */}
          {weightChartData.length > 1 && (
            <div className="card">
              <h4 style={{ marginBottom: 16 }}>Evolucao de Peso (kg)</h4>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={weightChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                  <XAxis dataKey="date" fontSize={11} />
                  <YAxis fontSize={11} domain={['auto', 'auto']} />
                  <Tooltip />
                  <Line type="monotone" dataKey="peso" stroke="#7dd3b4" strokeWidth={3} dot={{ fill: '#7dd3b4', r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Ultimas sessoes */}
          <div className="card">
            <h4 style={{ marginBottom: 16 }}>Ultimas sessoes</h4>
            {sessions.length === 0 ? <p style={{ color: 'var(--text-secondary)' }}>Nenhuma sessao.</p> : (
              sessions.slice(0, 5).map(s => (
                <div key={s.id} className="timeline-item">
                  <span className="date">{new Date(s.date).toLocaleDateString('pt-BR')}</span>
                  <p className="drug">{s.session_type}{s.drug_name ? ` - ${s.drug_name}` : ''}</p>
                  {s.dose_administered && <p style={{ fontSize: 13 }}>Dose: {s.dose_administered}mg ({s.dose_mg_m2} mg/m2) - Peso: {s.weight_at_session}kg</p>}
                  {s.notes && <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{s.notes}</p>}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Protocolos */}
      {subTab === 'protocolos' && (
        <ProtocolPanel pet={pet} canManage={true} onChanged={loadAll} />
      )}

      {/* Nova sessao */}
      {subTab === 'sessao' && (
        <div className="card">
          <h4 style={{ marginBottom: 20 }}>Registrar sessao</h4>
          <form onSubmit={handleSessionSubmit}>
            <label>Protocolo</label>
            <select value={sessionForm.protocol_id} onChange={e => handleProtocolSelect(e.target.value)}>
              <option value="">-- Sessao avulsa (sem protocolo) --</option>
              {activeProtocols.map(p => (
                <option key={p.id} value={p.id}>
                  {p.name} - sessao {p.executed_sessions + 1} de {p.planned_sessions}
                </option>
              ))}
            </select>
            <div className="grid-3">
              <div><label>Data</label><input type="date" value={sessionForm.date} onChange={e => setSessionForm({...sessionForm, date: e.target.value})} required /></div>
              <div><label>Tipo</label>
                <select value={sessionForm.session_type} onChange={e => setSessionForm({...sessionForm, session_type: e.target.value})}>
                  <option value="quimioterapia">Quimioterapia</option>
                  <option value="radioterapia">Radioterapia</option>
                  <option value="imunoterapia">Imunoterapia</option>
                </select>
              </div>
              <div><label>Peso no dia (kg)</label><input type="number" step="0.1" value={sessionForm.weight_at_session} onChange={e => setSessionForm({...sessionForm, weight_at_session: e.target.value})} required /></div>
            </div>
            <div className="grid-2">
              <div><label>Medicamento</label><input value={sessionForm.drug_name} onChange={e => setSessionForm({...sessionForm, drug_name: e.target.value})} placeholder="Ex: Doxorrubicina" /></div>
              <div><label>Dose (mg/m2)</label><input type="number" step="0.01" value={sessionForm.dose_mg_m2} onChange={e => setSessionForm({...sessionForm, dose_mg_m2: e.target.value})} /></div>
            </div>
            <label>Observacoes</label>
            <textarea value={sessionForm.notes} onChange={e => setSessionForm({...sessionForm, notes: e.target.value})} rows={3} />
            <button type="submit" className="primary" style={{ width: '100%', marginTop: 8 }}>Registrar</button>
          </form>
        </div>
      )}

      {/* Registros do tutor */}
      {subTab === 'registros' && (
        <div className="card">
          <h4 style={{ marginBottom: 16 }}>Registros do tutor</h4>
          {records.length === 0 ? <p style={{ color: 'var(--text-secondary)' }}>Nenhum registro do tutor ainda.</p> : (
            records.map(r => (
              <div key={r.id} className="timeline-item">
                <span className="date">{new Date(r.date).toLocaleDateString('pt-BR')}</span>
                <div style={{ marginTop: 4, fontSize: 14 }}>
                  {r.weight && <span><strong>Peso:</strong> {r.weight}kg </span>}
                  {r.general_status && <span className="badge badge-mint" style={{ marginRight: 6 }}>{r.general_status}</span>}
                  {r.appetite && <span className="badge badge-pink" style={{ marginRight: 6 }}>Apetite: {r.appetite}</span>}
                  {r.energy_level && <span className="badge badge-mint">Energia: {r.energy_level}</span>}
                </div>
                {r.symptoms && <p style={{ marginTop: 6, fontSize: 13 }}><strong>Sintomas:</strong> {r.symptoms}</p>}
                {r.notes && <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{r.notes}</p>}
              </div>
            ))
          )}
        </div>
      )}

      {/* Documentos */}
      {subTab === 'documentos' && (
        <div>
          <div className="card">
            <h4 style={{ marginBottom: 20 }}>Anexar documento</h4>

            <FileUpload onUploaded={(fileData) => {
              setDocForm({ ...docForm, file_url: fileData.url, title: docForm.title || fileData.filename })
            }} />

            {docForm.file_url && (
              <div style={{ background: 'var(--mint-light)', padding: 12, borderRadius: 8, marginBottom: 16, fontSize: 13 }}>
                Arquivo enviado: <strong>{docForm.file_url}</strong>
              </div>
            )}

            <form onSubmit={handleDocSubmit}>
              <div className="grid-2">
                <div><label>Titulo</label><input value={docForm.title} onChange={e => setDocForm({...docForm, title: e.target.value})} placeholder="Hemograma completo" required /></div>
                <div><label>Tipo</label>
                  <select value={docForm.doc_type} onChange={e => setDocForm({...docForm, doc_type: e.target.value})}>
                    <option value="exame_sangue">Exame de Sangue</option>
                    <option value="exame_imagem">Exame de Imagem</option>
                    <option value="laudo">Laudo</option>
                    <option value="outro">Outro</option>
                  </select>
                </div>
              </div>
              <div className="grid-2">
                <div><label>Data</label><input type="date" value={docForm.date} onChange={e => setDocForm({...docForm, date: e.target.value})} /></div>
                <div><label>URL (ou use o upload acima)</label><input value={docForm.file_url} onChange={e => setDocForm({...docForm, file_url: e.target.value})} placeholder="Preenchido automaticamente" required /></div>
              </div>
              <label>Notas</label>
              <textarea value={docForm.notes} onChange={e => setDocForm({...docForm, notes: e.target.value})} rows={2} />
              <button type="submit" className="secondary" style={{ marginTop: 8 }}>Salvar Documento</button>
            </form>
          </div>

          {documents.length > 0 && (
            <div className="card">
              <h4 style={{ marginBottom: 16 }}>Documentos anexados</h4>
              {documents.map(d => (
                <div key={d.id} className="doc-item">
                  <div style={{ flex: 1 }}>
                    <strong>{d.title}</strong>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      {d.doc_type.replace('_', ' ')} {d.date && `- ${new Date(d.date).toLocaleDateString('pt-BR')}`}
                    </div>
                  </div>
                  <a href={d.file_url} target="_blank" rel="noreferrer">
                    <button className="outline" style={{ padding: '6px 12px', fontSize: 12 }}>Abrir</button>
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Agenda - vet pode criar lembretes */}
      {subTab === 'agenda' && (
        <PetAgenda pet={pet} canCreate={true} />
      )}
    </div>
  )
}

export default PetDetail
