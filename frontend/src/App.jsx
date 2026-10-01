import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { SESSION_EXPIRED } from './api'
import Login from './pages/Login'
import VetDashboard from './pages/VetDashboard'
import TutorDashboard from './pages/TutorDashboard'
import { LogoMark } from './components/Logo'

// Versoes anteriores guardavam o token no localStorage: apaga o que sobrou
function clearOldStorage() {
  try {
    localStorage.removeItem('oncopet_token')
    localStorage.removeItem('oncopet_user')
  } catch { /* navegador sem localStorage */ }
}

function App() {
  // Quem esta logado vem da API (cookie HttpOnly), nao do navegador
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    clearOldStorage()
    api.get('/auth/me')
      .then(res => setUser(res.data))
      .catch(() => setUser(null))
      .finally(() => setChecking(false))

    const onExpired = () => setUser(null)
    window.addEventListener(SESSION_EXPIRED, onExpired)
    return () => window.removeEventListener(SESSION_EXPIRED, onExpired)
  }, [])

  const handleLogin = (userData) => setUser(userData)

  const handleLogout = async () => {
    try { await api.post('/auth/logout') } catch { /* sai mesmo assim */ }
    setUser(null)
    navigate('/', { replace: true })
  }

  if (checking) {
    return (
      <div className="app-loading" aria-busy="true">
        <LogoMark size={72} title="Carregando o OncoPet" />
      </div>
    )
  }

  // Sem login: mostra o Login em qualquer URL; depois de entrar, a mesma URL e aberta
  if (!user) {
    return <Login onLogin={handleLogin} />
  }

  if (user.role === 'vet') {
    return <VetDashboard user={user} onLogout={handleLogout} />
  }

  return <TutorDashboard user={user} onLogout={handleLogout} />
}

export default App
