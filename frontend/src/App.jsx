import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Login from './pages/Login'
import VetDashboard from './pages/VetDashboard'
import TutorDashboard from './pages/TutorDashboard'

function App() {
  const [token, setToken] = useState(localStorage.getItem('oncopet_token'))
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('oncopet_user') || 'null'))
  const navigate = useNavigate()

  const handleLogin = (newToken, userData) => {
    localStorage.setItem('oncopet_token', newToken)
    localStorage.setItem('oncopet_user', JSON.stringify(userData))
    setToken(newToken)
    setUser(userData)
  }

  const handleLogout = () => {
    localStorage.removeItem('oncopet_token')
    localStorage.removeItem('oncopet_user')
    setToken(null)
    setUser(null)
    navigate('/', { replace: true })
  }

  // Sem login: mostra o Login em qualquer URL; depois de entrar, a mesma URL e aberta
  if (!token || !user) {
    return <Login onLogin={handleLogin} />
  }

  if (user.role === 'vet') {
    return <VetDashboard user={user} onLogout={handleLogout} />
  }

  return <TutorDashboard user={user} onLogout={handleLogout} />
}

export default App
