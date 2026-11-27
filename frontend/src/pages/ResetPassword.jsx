import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle2 } from 'lucide-react'
import api, { getErrorMessage } from '../api'
import { LogoMark } from '../components/Logo'

const MIN_LENGTH = 6

/**
 * Pagina aberta pelo link do e-mail (/redefinir-senha?token=...).
 * Funciona sem login: o token do link e que autoriza a troca.
 */
function ResetPassword() {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  const [saving, setSaving] = useState(false)

  const goToLogin = () => navigate('/', { replace: true })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (password.length < MIN_LENGTH) {
      setError(`A senha precisa ter pelo menos ${MIN_LENGTH} caracteres.`)
      return
    }
    if (password !== confirm) {
      setError('As duas senhas não são iguais.')
      return
    }
    setSaving(true)
    try {
      await api.post('/auth/reset-password', { token, new_password: password })
      setDone(true)
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível trocar a senha agora. Tente de novo.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-logo"><LogoMark size={96} title="" /></div>
        <h2>Nova senha</h2>

        {!token ? (
          <>
            <p className="error" style={{ marginTop: 24 }}>Este link está incompleto. Peça um novo em "Esqueci minha senha".</p>
            <button className="primary" onClick={goToLogin} style={{ width: '100%', padding: 14 }}>Ir para o login</button>
          </>
        ) : done ? (
          <>
            <div className="success-msg" role="status" style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 24 }}>
              <CheckCircle2 size={22} style={{ flexShrink: 0 }} aria-hidden="true" />
              <span>Senha alterada! Agora é só entrar com a nova senha.</span>
            </div>
            <button className="primary" onClick={goToLogin} style={{ width: '100%', padding: 14 }}>Ir para o login</button>
          </>
        ) : (
          <>
            <p style={{ textAlign: 'center', marginBottom: 28, color: 'var(--text-secondary)', fontSize: 14 }}>
              Escolha uma senha nova, com pelo menos {MIN_LENGTH} caracteres.
            </p>
            <form onSubmit={handleSubmit}>
              <label htmlFor="reset-password">Nova senha</label>
              <input
                id="reset-password" type="password" autoComplete="new-password" required autoFocus
                value={password} onChange={(e) => setPassword(e.target.value)}
              />
              <label htmlFor="reset-confirm">Repita a nova senha</label>
              <input
                id="reset-confirm" type="password" autoComplete="new-password" required
                value={confirm} onChange={(e) => setConfirm(e.target.value)}
              />
              {error && <p className="error">{error}</p>}
              <button type="submit" className="primary" disabled={saving} style={{ width: '100%', marginTop: 12, padding: 14 }}>
                {saving ? 'Salvando...' : 'Salvar nova senha'}
              </button>
            </form>
            <p style={{ textAlign: 'center', marginTop: 24 }}>
              <button className="ghost" onClick={goToLogin}>Voltar para o login</button>
            </p>
          </>
        )}
      </div>
    </div>
  )
}

export default ResetPassword
