import { useState, useEffect } from 'react'
import api, { getErrorMessage } from '../api'
import { useLocation, useNavigate, matchPath, Navigate } from 'react-router-dom'
import { PawPrint, CirclePlus, Building2, ClipboardList } from 'lucide-react'
import PetDetail, { PET_TABS } from '../components/PetDetail'
import AppHeader from '../components/AppHeader'
import PetAvatar from '../components/PetAvatar'
import PhotoField from '../components/PhotoField'
import { uploadPetPhoto } from '../image'

/**
 * Rotas do veterinario:
 *   /pacientes               lista
 *   /pacientes/novo          cadastro
 *   /clinica                 clinicas
 *   /pacientes/:petId/:aba?  prontuario (aba: dashboard, protocolos, sessao...)
 * Retorna null para URL desconhecida (redireciona para /pacientes).
 */
export function parseVetRoute(pathname) {
  const path = pathname.replace(/\/+$/, '') || '/'
  if (path === '/pacientes') return { tab: 'pacientes' }
  if (path === '/pacientes/novo') return { tab: 'cadastro' }
  if (path === '/clinica') return { tab: 'clinica' }
  const match = matchPath('/pacientes/:petId/:aba?', path)
  if (match && /^\d+$/.test(match.params.petId)) {
    const aba = match.params.aba || 'dashboard'
    if (PET_TABS.includes(aba)) return { tab: 'prontuario', petId: Number(match.params.petId), aba }
  }
  return null
}

function VetDashboard({ user, onLogout }) {
  const [pets, setPets] = useState([])
  const [tutors, setTutors] = useState([])
  const [clinics, setClinics] = useState([])
  const [loaded, setLoaded] = useState(false)
  const [lastPetId, setLastPetId] = useState(null)
  const [photoFile, setPhotoFile] = useState(null)
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

  // Tela atual vem da URL (voltar do navegador e F5 funcionam)
  const location = useLocation()
  const navigate = useNavigate()
  const route = parseVetRoute(location.pathname)
  const activeTab = route?.tab
  const selectedPet = route?.petId ? pets.find(p => p.id === route.petId) : null

  useEffect(() => {
    loadAll()
  }, [])

  useEffect(() => {
    if (route?.petId) setLastPetId(route.petId)
  }, [route?.petId])

  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [activeTab, route?.petId])

  const goTo = (tab) => {
    const paths = {
      pacientes: '/pacientes',
      cadastro: '/pacientes/novo',
      clinica: '/clinica',
      prontuario: `/pacientes/${lastPetId}`,
    }
    navigate(paths[tab])
  }

  const goToPetTab = (petId, aba) => {
    navigate(aba === 'dashboard' ? `/pacientes/${petId}` : `/pacientes/${petId}/${aba}`)
  }

  const loadAll = async () => {
    try {
      const [p, t, c, b] = await Promise.all([
        api.get('/pets/'), api.get('/tutors/'), api.get('/clinics/'), api.get('/pets/breeds')
      ])
      setPets(p.data); setTutors(t.data); setClinics(c.data); setBreeds(b.data)
    } catch (err) { console.error(err) }
    finally { setLoaded(true) }
  }

  const currentBreeds = petForm.species.includes('gato') ? breeds.cats : breeds.dogs

  const handlePetSubmit = async (e) => {
    e.preventDefault(); setError('')
    try {
      const res = await api.post('/pets/', {
        ...petForm,
        weight: parseFloat(petForm.weight),
        age_years: petForm.age_years ? parseInt(petForm.age_years) : null,
        age_months: petForm.age_months ? parseInt(petForm.age_months) : null,
        tutor_id: parseInt(petForm.tutor_id),
        clinic_id: petForm.clinic_id ? parseInt(petForm.clinic_id) : null,
        treatment_start_date: petForm.treatment_start_date || null,
      })
      // Foto e opcional: se falhar, o pet ja foi cadastrado e so avisamos
      if (photoFile) {
        try {
          await uploadPetPhoto(api, res.data.id, photoFile)
        } catch (photoErr) {
          setError(`Cadastrado, mas a foto nao foi enviada: ${photoErr.response ? getErrorMessage(photoErr) : photoErr.message}`)
        }
        setPhotoFile(null)
      }
      setPetForm({ name: '', species: 'cao', breed: '', weight: '', age_years: '', age_months: '', cancer_type: '', treatment_start_date: '', tutor_id: '', clinic_id: '' })
      setSuccess('Paciente cadastrado!'); setTimeout(() => setSuccess(''), 3000)
      loadAll()
    } catch (err) { setError(getErrorMessage(err)) }
  }

  const handleClinicSubmit = async (e) => {
    e.preventDefault(); setError('')
    try {
      await api.post('/clinics/', clinicForm)
      setClinicForm({ name: '', address: '', phone: '' })
      setSuccess('Clinica cadastrada!'); setTimeout(() => setSuccess(''), 3000)
      loadAll()
    } catch (err) { setError(getErrorMessage(err)) }
  }

  if (!route) return <Navigate to="/pacientes" replace />

  return (
    <div className="container">
      <AppHeader role="vet" userName={user.full_name} onLogout={onLogout} />

      <nav className="nav-tabs">
        <button className={activeTab === 'pacientes' ? 'active' : ''} onClick={() => goTo('pacientes')}>
          <PawPrint /><span className="label-long">Pacientes</span><span className="label-short">Pacientes</span>
        </button>
        <button className={activeTab === 'cadastro' ? 'active' : ''} onClick={() => goTo('cadastro')}>
          <CirclePlus /><span className="label-long">Novo Paciente</span><span className="label-short">Novo</span>
        </button>
        <button className={activeTab === 'clinica' ? 'active' : ''} onClick={() => goTo('clinica')}>
          <Building2 /><span className="label-long">Clinica</span><span className="label-short">Clinica</span>
        </button>
        <button className={activeTab === 'prontuario' ? 'active' : ''} onClick={() => goTo('prontuario')} disabled={!lastPetId}>
          <ClipboardList /><span className="label-long">Prontuario</span><span className="label-short">Prontuario</span>
        </button>
      </nav>

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
              <div key={pet.id} className={`pet-card ${lastPetId === pet.id ? 'selected' : ''}`}
                onClick={() => goToPetTab(pet.id, 'dashboard')}>
                <PetAvatar pet={pet} />
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
            <PhotoField file={photoFile} onChange={setPhotoFile} />
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
        <PetDetail
          pet={selectedPet}
          onUpdated={loadAll}
          subTab={route.aba}
          onSubTabChange={(aba) => goToPetTab(selectedPet.id, aba)}
        />
      )}
      {activeTab === 'prontuario' && !selectedPet && loaded && (
        <div className="card empty-state">
          <h3>Paciente nao encontrado</h3>
          <p>Ele pode ter sido removido ou nao esta atribuido a voce.</p>
          <button className="primary" style={{ marginTop: 16 }} onClick={() => goTo('pacientes')}>Ver pacientes</button>
        </div>
      )}
    </div>
  )
}

export default VetDashboard
