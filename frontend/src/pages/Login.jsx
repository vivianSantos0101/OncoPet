import { useState } from 'react'
import api from '../api'

function Login({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false)
  const [role, setRole] = useState('vet')
  const [form, setForm] = useState({
    username: '', password: '', full_name: '',
    email: '', phone: '', crmv: '',
  })
  const [error, setError] = useState('')

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      if (isRegister) {
        const payload = { ...form, role }
        if (role !== 'vet') delete payload.crmv
        const res = await api.post('/auth/register', payload)
        onLogin(res.data.access_token, res.data.user)
      } else {
        const formData = new URLSearchParams()
        formData.append('username', form.username)
        formData.append('password', form.password)
        const res = await api.post('/auth/login', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        })
        onLogin(res.data.access_token, res.data.user)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro de conexao')
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>OncoVet</h2>
        <p style={{ textAlign: 'center', marginBottom: 32, color: 'var(--text-secondary)', fontSize: 14 }}>
          Gestao de Oncologia Veterinaria
        </p>

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <div className="role-selector">
                <button
                  type="button"
                  className={role === 'vet' ? 'active-vet' : ''}
                  onClick={() => setRole('vet')}
                >
                  Veterinario
                </button>
                <button
                  type="button"
                  className={role === 'tutor' ? 'active-tutor' : ''}
                  onClick={() => setRole('tutor')}
                >
                  Tutor
                </button>
              </div>

              <label>Nome Completo</label>
              <input name="full_name" value={form.full_name} onChange={handleChange} required />

              <div className="grid-2">
                <div>
                  <label>Email</label>
                  <input name="email" type="email" value={form.email} onChange={handleChange} />
                </div>
                <div>
                  <label>Telefone</label>
                  <input name="phone" value={form.phone} onChange={handleChange} placeholder="(11) 99999-9999" />
                </div>
              </div>

              {role === 'vet' && (
                <>
                  <label>CRMV</label>
                  <input name="crmv" value={form.crmv} onChange={handleChange} placeholder="SP-12345" />
                </>
              )}
            </>
          )}

          <label>Usuario</label>
          <input name="username" value={form.username} onChange={handleChange} required />
          <label>Senha</label>
          <input name="password" type="password" value={form.password} onChange={handleChange} required />

          {error && <p className="error">{error}</p>}

          <button type="submit" className="primary" style={{ width: '100%', marginTop: 12, padding: 14 }}>
            {isRegister ? 'Criar Conta' : 'Entrar'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 24 }}>
          <button className="ghost" onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? 'Ja tem conta? Entrar' : 'Criar uma conta'}
          </button>
        </p>
      </div>
    </div>
  )
}

export default Login
