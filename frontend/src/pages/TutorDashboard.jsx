import { useState, useEffect } from 'react'
import api, { getErrorMessage } from '../api'
import Notifications from '../components/Notifications'
import { PawPrint, CirclePlus, NotebookPen, Activity, CalendarDays } from 'lucide-react'
import PetAgenda from '../components/PetAgenda'
import AppHeader from '../components/AppHeader'
import ProtocolPanel from '../components/ProtocolPanel'

function TutorDashboard({ user, onLogout }) {
  const [pets, setPets] = useState([])
  const [selectedPet, setSelectedPet] = useState(null)
  const [records, setRecords] = useState([])
  const [activeTab, setActiveTab] = useState('pets')
  const [breeds, setBreeds] = useState({ dogs: [], cats: [] })
  const [vets, setVets] = useState([])
  const [clinics, setClinics] = useState([])

  // Forms
  const [petForm, setPetForm] = useState({
    name: '', species: 'cao', breed: '', weight: '',
    age_years: '', age_months: '', cancer_type: '',
    treatment_start_date: '', vet_id: '', clinic_id: '',
  })
  const [recordForm, setRecordForm] = useState({
    date: new Date().toISOString().split('T')[0],
    weight: '', symptoms: '', general_status: '',
    appetite: '', energy_level: '', notes: '',
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    loadPets()
    api.get('/pets/breeds').then(r => setBreeds(r.data)).catch(() => {})
    api.get('/vets/').then(r => setVets(r.data)).catch(() => {})
    api.get('/clinics/').then(r => setClinics(r.data)).catch(() => {})
  }, [])

  const loadPets = async () => {
    const res = await api.get('/pets/')
    setPets(res.data)
  }

  const loadRecords = async (petId) => {
    const res = await api.get(`/records/pet/${petId}`)
    setRecords(res.data)
  }

  const selectPet = (pet) => {
    setSelectedPet(pet)
    loadRecords(pet.id)
    setRecordForm({ ...recordForm, weight: String(pet.weight) })
    setActiveTab('diario')
  }

  const currentBreeds = petForm.species.includes('gato') ? breeds.cats : breeds.dogs

  const handlePetSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/pets/', {
        ...petForm,
        weight: parseFloat(petForm.weight),
        age_years: petForm.age_years ? parseInt(petForm.age_years) : null,
        age_months: petForm.age_months ? parseInt(petForm.age_months) : null,
        vet_id: petForm.vet_id ? parseInt(petForm.vet_id) : null,
        clinic_id: petForm.clinic_id ? parseInt(petForm.clinic_id) : null,
        treatment_start_date: petForm.treatment_start_date || null,
      })
      setPetForm({ name: '', species: 'cao', breed: '', weight: '', age_years: '', age_months: '', cancer_type: '', treatment_start_date: '', vet_id: '', clinic_id: '' })
      setSuccess('Animal cadastrado!')
      setTimeout(() => setSuccess(''), 3000)
      loadPets()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const handleRecordSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await api.post('/records/', {
        pet_id: selectedPet.id,
        date: recordForm.date,
        weight: recordForm.weight ? parseFloat(recordForm.weight) : null,
        symptoms: recordForm.symptoms || null,
        general_status: recordForm.general_status || null,
        appetite: recordForm.appetite || null,
        energy_level: recordForm.energy_level || null,
        notes: recordForm.notes || null,
      })
      setSuccess('Registro salvo!')
      setTimeout(() => setSuccess(''), 3000)
      setRecordForm({ ...recordForm, symptoms: '', general_status: '', appetite: '', energy_level: '', notes: '' })
      loadRecords(selectedPet.id)
      loadPets()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="container">
      <Notifications />
      <AppHeader role="tutor" userName={user.full_name} onLogout={onLogout} />

      <nav className="nav-tabs">
        <button className={activeTab === 'pets' ? 'active' : ''} onClick={() => setActiveTab('pets')}>
          <PawPrint /><span className="label-long">Meus Animais</span><span className="label-short">Animais</span>
        </button>
        <button className={activeTab === 'novo' ? 'active' : ''} onClick={() => setActiveTab('novo')}>
          <CirclePlus /><span className="label-long">Cadastrar Animal</span><span className="label-short">Novo</span>
        </button>
        <button className={activeTab === 'diario' ? 'active' : ''} onClick={() => setActiveTab('diario')} disabled={!selectedPet}>
          <NotebookPen /><span className="label-long">Diario</span><span className="label-short">Diario</span>
        </button>
        <button className={activeTab === 'tratamento' ? 'active' : ''} onClick={() => setActiveTab('tratamento')} disabled={!selectedPet}>
          <Activity /><span className="label-long">Tratamento</span><span className="label-short">Tratamento</span>
        </button>
        <button className={activeTab === 'agenda' ? 'active' : ''} onClick={() => setActiveTab('agenda')} disabled={!selectedPet}>
          <CalendarDays /><span className="label-long">Agenda</span><span className="label-short">Agenda</span>
        </button>
      </nav>

      {error && <p className="error">{error}</p>}
      {success && <div className="success-msg">{success}</div>}

      {/* Lista de pets */}
      {activeTab === 'pets' && (
        <div>
          {pets.length === 0 ? (
            <div className="card empty-state">
              <h3>Nenhum animal cadastrado</h3>
              <p>Cadastre seu primeiro animal para comecar o acompanhamento.</p>
            </div>
          ) : (
            pets.map(pet => (
              <div key={pet.id} className={`pet-card ${selectedPet?.id === pet.id ? 'selected' : ''}`} onClick={() => selectPet(pet)}>
                <div className="pet-avatar">{pet.name.charAt(0).toUpperCase()}</div>
                <div style={{ flex: 1 }}>
                  <strong style={{ fontSize: 16 }}>{pet.name}</strong>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>
                    {pet.breed} - {pet.weight}kg
                    {pet.cancer_type && ` - ${pet.cancer_type}`}
                  </div>
                </div>
                <span className="badge badge-mint">{pet.species}</span>
              </div>
            ))
          )}
        </div>
      )}

      {/* Cadastrar pet */}
      {activeTab === 'novo' && (
        <div className="card">
          <h3 style={{ marginBottom: 24 }}>Cadastrar novo animal</h3>
          <form onSubmit={handlePetSubmit}>
            <div className="grid-2">
              <div><label>Nome</label><input value={petForm.name} onChange={e => setPetForm({...petForm, name: e.target.value})} required /></div>
              <div><label>Especie</label>
                <select value={petForm.species} onChange={e => setPetForm({...petForm, species: e.target.value, breed: ''})}>
                  <option value="cao">Cao</option><option value="gato">Gato</option>
                </select>
              </div>
            </div>
            <div className="grid-2">
              <div><label>Raca</label>
                <select value={petForm.breed} onChange={e => setPetForm({...petForm, breed: e.target.value})} required>
                  <option value="">-- Selecione --</option>
                  {currentBreeds.map(b => <option key={b} value={b}>{b}</option>)}
                </select>
              </div>
              <div><label>Peso (kg)</label><input type="number" step="0.1" min="0.1" max="150" value={petForm.weight} onChange={e => setPetForm({...petForm, weight: e.target.value})} required /></div>
            </div>
            <div className="grid-3">
              <div><label>Idade (anos)</label><input type="number" min="0" max="40" value={petForm.age_years} onChange={e => setPetForm({...petForm, age_years: e.target.value})} /></div>
              <div><label>Idade (meses)</label><input type="number" min="0" max="11" value={petForm.age_months} onChange={e => setPetForm({...petForm, age_months: e.target.value})} /></div>
              <div><label>Tipo de Cancer</label><input value={petForm.cancer_type} onChange={e => setPetForm({...petForm, cancer_type: e.target.value})} /></div>
            </div>
            <div className="grid-3">
              <div><label>Inicio Tratamento</label><input type="date" value={petForm.treatment_start_date} onChange={e => setPetForm({...petForm, treatment_start_date: e.target.value})} /></div>
              <div><label>Veterinario</label>
                <select value={petForm.vet_id} onChange={e => setPetForm({...petForm, vet_id: e.target.value})}>
                  <option value="">-- Opcional --</option>
                  {vets.map(v => <option key={v.id} value={v.id}>{v.full_name}</option>)}
                </select>
              </div>
              <div><label>Clinica</label>
                <select value={petForm.clinic_id} onChange={e => setPetForm({...petForm, clinic_id: e.target.value})}>
                  <option value="">-- Opcional --</option>
                  {clinics.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            </div>
            <button type="submit" className="primary" style={{ marginTop: 8 }}>Cadastrar</button>
          </form>
        </div>
      )}

      {/* Diario do pet */}
      {activeTab === 'diario' && selectedPet && (
        <div>
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div className="pet-avatar" style={{ width: 56, height: 56, fontSize: 22 }}>
              {selectedPet.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3>{selectedPet.name}</h3>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                {selectedPet.breed} - {selectedPet.weight}kg - SC: {selectedPet.body_surface_area} m2
              </p>
            </div>
          </div>

          <div className="card">
            <h4 style={{ marginBottom: 20 }}>Novo registro diario</h4>
            <form onSubmit={handleRecordSubmit}>
              <div className="grid-3">
                <div><label>Data</label><input type="date" value={recordForm.date} onChange={e => setRecordForm({...recordForm, date: e.target.value})} required /></div>
                <div><label>Peso (kg)</label><input type="number" step="0.1" min="0.1" max="150" value={recordForm.weight} onChange={e => setRecordForm({...recordForm, weight: e.target.value})} /></div>
                <div><label>Estado Geral</label>
                  <select value={recordForm.general_status} onChange={e => setRecordForm({...recordForm, general_status: e.target.value})}>
                    <option value="">--</option>
                    <option value="otimo">Otimo</option><option value="bom">Bom</option>
                    <option value="regular">Regular</option><option value="ruim">Ruim</option>
                  </select>
                </div>
              </div>
              <div className="grid-2">
                <div><label>Apetite</label>
                  <select value={recordForm.appetite} onChange={e => setRecordForm({...recordForm, appetite: e.target.value})}>
                    <option value="">--</option>
                    <option value="normal">Normal</option><option value="reduzido">Reduzido</option>
                    <option value="ausente">Ausente</option>
                  </select>
                </div>
                <div><label>Energia</label>
                  <select value={recordForm.energy_level} onChange={e => setRecordForm({...recordForm, energy_level: e.target.value})}>
                    <option value="">--</option>
                    <option value="alto">Alto</option><option value="normal">Normal</option>
                    <option value="baixo">Baixo</option><option value="letargico">Letargico</option>
                  </select>
                </div>
              </div>
              <label>Sintomas</label>
              <textarea value={recordForm.symptoms} onChange={e => setRecordForm({...recordForm, symptoms: e.target.value})} rows={2} placeholder="Descreva sintomas observados..." />
              <label>Observacoes</label>
              <textarea value={recordForm.notes} onChange={e => setRecordForm({...recordForm, notes: e.target.value})} rows={2} placeholder="Notas livres..." />
              <button type="submit" className="secondary" style={{ width: '100%', marginTop: 8 }}>Salvar Registro</button>
            </form>
          </div>

          <div className="card">
            <h4 style={{ marginBottom: 16 }}>Historico de registros</h4>
            {records.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)' }}>Nenhum registro ainda.</p>
            ) : (
              records.map(r => (
                <div key={r.id} className="timeline-item">
                  <span className="date">{new Date(r.date).toLocaleDateString('pt-BR')}</span>
                  <div style={{ marginTop: 4, fontSize: 14 }}>
                    {r.weight && <span><strong>Peso:</strong> {r.weight}kg </span>}
                    {r.general_status && <span className="badge badge-mint" style={{ marginRight: 6 }}>{r.general_status}</span>}
                    {r.appetite && <span className="badge badge-pink">{r.appetite}</span>}
                  </div>
                  {r.symptoms && <p style={{ marginTop: 6, fontSize: 13 }}><strong>Sintomas:</strong> {r.symptoms}</p>}
                  {r.notes && <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{r.notes}</p>}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Progresso do protocolo (somente leitura) */}
      {activeTab === 'tratamento' && selectedPet && (
        <ProtocolPanel pet={selectedPet} />
      )}

      {/* Agenda do pet */}
      {activeTab === 'agenda' && selectedPet && (
        <PetAgenda pet={selectedPet} canCreate={false} />
      )}
    </div>
  )
}

export default TutorDashboard
