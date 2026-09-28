import { useState, useEffect } from 'react'
import api from '../api'
import PetDetail from '../components/PetDetail'

function VetDashboard({ user, onLogout }) {
  const [pets, setPets] = useState([])
  const [tutors, setTutors] = useState([])
  const [clinics, setClinics] = useState([])
  const [selectedPet, setSelectedPet] = useState(null)
  const [activeTab, setActiveTab] = useState('pacientes')
  const [breeds, setBreeds] = useState({ dogs: [], cats: [] })

  // Forms
  const [petForm, setPetForm] = useState({
    name: '', species: 'cao', breed: '', weight: '',
    age_years: '', age_months: '', cancer_type: '',
    treatment_start_date: '', tutor_id: '', clinic_id: '',
  })
  const [clinicForm, setClinicForm] = useState({ name: '', address: '', phone: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    loadAll()
  }, [])

  const loadAll = async () => {
    try {
      const [p, t, c, b] = await Promise.all([
        api.get('/pets/'), api.get('/tutors/'), api.get('/clinics/'), api.get('/pets/breeds')
      ])
      setPets(p.data); setTutors(t.data); setClinics(c.data); setBreeds(b.data)
    } catch (err) { console.error(err) }
  }

  const currentBreeds = petForm.species.includes('gato') ? breeds.cats : breeds.dogs

  const handlePetSubmit = async (e) => {
    e.preventDefault(); setError('')
    try {
      await api.post('/pets/', {
        ...petForm,
        weight: parseFloat(petForm.weight),
        age_years: petForm.age_years ? parseInt(petForm.age_years) : null,
        age_months: petForm.age_months ? parseInt(petForm.age_months) : null,
        tutor_id: parseInt(petForm.tutor_id),
        clinic_id: petForm.clinic_id ? parseInt(petForm.clinic_id) : null,
        treatment_start_date: petForm.treatment_start_date || null,
      })
      setPetForm({ name: '', species: 'cao', breed: '', weight: '', age_years: '', age_months: '', cancer_type: '', treatment_start_date: '', tutor_id: '', clinic_id: '' })
      setSuccess('Paciente cadastrado!'); setTimeout(() => setSuccess(''), 3000)
      loadAll()
    } catch (err) { setError(err.response?.data?.detail || 'Erro') }
  }

  const handleClinicSubmit = async (e) => {
    e.preventDefault(); setError('')
    try {
      await api.post('/clinics/', clinicForm)
      setClinicForm({ name: '', address: '', phone: '' })
      setSuccess('Clinica cadastrada!'); setTimeout(() => setSuccess(''), 3000)
      loadAll()
    } catch (err) { setError(err.response?.data?.detail || 'Erro') }
  }

  return (
    <div className="container">
      <div className="header">
        <h1>OncoVet</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="role-badge vet">Veterinario</span>
          <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{user.full_name}</span>
          <button className="danger" onClick={onLogout} style={{ padding: '8px 16px', fontSize: 12 }}>Sair</button>
        </div>
      </div>

      <div className="nav-tabs">
        <button className={activeTab === 'pacientes' ? 'active' : ''} onClick={() => setActiveTab('pacientes')}>Pacientes</button>
        <button className={activeTab === 'cadastro' ? 'active' : ''} onClick={() => setActiveTab('cadastro')}>Novo Paciente</button>
        <button className={activeTab === 'clinica' ? 'active' : ''} onClick={() => setActiveTab('clinica')}>Clinica</button>
        <button className={activeTab === 'prontuario' ? 'active' : ''} onClick={() => setActiveTab('prontuario')} disabled={!selectedPet}>Prontuario</button>
      </div>

      {error && <p className="error">{error}</p>}
      {success && <div className="success-msg">{success}</div>}

      {/* Pacientes */}
      {activeTab === 'pacientes' && (
        <div>
          {pets.length === 0 ? (
            <div className="card empty-state">
              <h3>Nenhum paciente</h3>
              <p>Cadastre pacientes para ver aqui.</p>
            </div>
          ) : (
            pets.map(pet => (
              <div key={pet.id} className={`pet-card ${selectedPet?.id === pet.id ? 'selected' : ''}`}
                onClick={() => { setSelectedPet(pet); setActiveTab('prontuario') }}>
                <div className="pet-avatar">{pet.species.includes('gato') ? 'G' : 'C'}</div>
                <div style={{ flex: 1 }}>
                  <strong style={{ fontSize: 16 }}>{pet.name}</strong>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>
                    {pet.breed} - {pet.weight}kg
                    {pet.cancer_type && ` - ${pet.cancer_type}`}
                    {pet.tutor_name && ` | Tutor: ${pet.tutor_name}`}
                  </div>
                </div>
                <span className="badge badge-mint">{pet.species}</span>
              </div>
            ))
          )}
        </div>
      )}

      {/* Cadastro de paciente */}
      {activeTab === 'cadastro' && (
        <div className="card">
          <h3 style={{ marginBottom: 24 }}>Cadastrar paciente</h3>
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
              <div><label>Peso (kg)</label><input type="number" step="0.1" value={petForm.weight} onChange={e => setPetForm({...petForm, weight: e.target.value})} required /></div>
            </div>
            <div className="grid-3">
              <div><label>Idade (anos)</label><input type="number" value={petForm.age_years} onChange={e => setPetForm({...petForm, age_years: e.target.value})} /></div>
              <div><label>Idade (meses)</label><input type="number" value={petForm.age_months} onChange={e => setPetForm({...petForm, age_months: e.target.value})} /></div>
              <div><label>Tipo de Cancer</label><input value={petForm.cancer_type} onChange={e => setPetForm({...petForm, cancer_type: e.target.value})} /></div>
            </div>
            <div className="grid-3">
              <div><label>Inicio Tratamento</label><input type="date" value={petForm.treatment_start_date} onChange={e => setPetForm({...petForm, treatment_start_date: e.target.value})} /></div>
              <div><label>Tutor</label>
                <select value={petForm.tutor_id} onChange={e => setPetForm({...petForm, tutor_id: e.target.value})} required>
                  <option value="">-- Selecione --</option>
                  {tutors.map(t => <option key={t.id} value={t.id}>{t.full_name}</option>)}
                </select>
              </div>
              <div><label>Clinica</label>
                <select value={petForm.clinic_id} onChange={e => setPetForm({...petForm, clinic_id: e.target.value})}>
                  <option value="">-- Opcional --</option>
                  {clinics.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            </div>
            <button type="submit" className="primary" style={{ marginTop: 8 }}>Cadastrar Paciente</button>
          </form>
        </div>
      )}

      {/* Clinica */}
      {activeTab === 'clinica' && (
        <div className="card">
          <h3 style={{ marginBottom: 24 }}>Cadastrar Clinica</h3>
          <form onSubmit={handleClinicSubmit}>
            <label>Nome</label><input value={clinicForm.name} onChange={e => setClinicForm({...clinicForm, name: e.target.value})} required />
            <div className="grid-2">
              <div><label>Endereco</label><input value={clinicForm.address} onChange={e => setClinicForm({...clinicForm, address: e.target.value})} /></div>
              <div><label>Telefone</label><input value={clinicForm.phone} onChange={e => setClinicForm({...clinicForm, phone: e.target.value})} /></div>
            </div>
            <button type="submit" className="primary">Cadastrar Clinica</button>
          </form>

          {clinics.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <h4 style={{ marginBottom: 12 }}>Clinicas cadastradas</h4>
              {clinics.map(c => (
                <div key={c.id} className="doc-item">
                  <strong>{c.name}</strong>
                  {c.address && <span style={{ color: 'var(--text-secondary)', marginLeft: 12 }}>{c.address}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Prontuario */}
      {activeTab === 'prontuario' && selectedPet && (
        <PetDetail pet={selectedPet} onUpdated={loadAll} />
      )}
    </div>
  )
}

export default VetDashboard
