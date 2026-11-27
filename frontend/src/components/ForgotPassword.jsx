import { useState } from 'react'
import { MailCheck } from 'lucide-react'
import api, { getErrorMessage } from '../api'
import { LogoMark } from './Logo'

/**
 * "Esqueci minha senha": pede o e-mail do cadastro e o backend manda um link.
 * A mensagem de sucesso e sempre a mesma, exista ou nao uma conta com o e-mail.
 */
function ForgotPassword({ onBack }) {
  const [email, setEmail] = useState('')
  const [sentMessage, setSentMessage] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSending(true)
    try {
      const res = await api.post('/auth/forgot-password', { email })
      setSentMessage(res.data.message)
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível enviar agora. Tente de novo.'))
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-logo"><LogoMark size={96} title="" /></div>
        <h2>Esqueci minha senha</h2>

        {sentMessage ? (
          <>
            <div className="success-msg" role="status" style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginTop: 24 }}>
              <MailCheck size={22} style={{ flexShrink: 0 }} aria-hidden="true" />
              <span>{sentMessage}</span>
            </div>
            <p style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: 14 }}>
              Confira também a caixa de spam.
            </p>
          </>
        ) : (
          <>
            <p style={{ textAlign: 'center', marginBottom: 28, color: 'var(--text-secondary)', fontSize: 14 }}>
              Digite o e-mail do seu cadastro. Vamos enviar um link para você criar uma nova senha.
            </p>
            <form onSubmit={handleSubmit}>
              <label htmlFor="forgot-email">E-mail</label>
              <input
                id="forgot-email" type="email" autoComplete="email" required autoFocus
                value={email} onChange={(e) => setEmail(e.target.value)}
              />
              {error && <p className="error">{error}</p>}
              <button type="submit" className="primary" disabled={sending} style={{ width: '100%', marginTop: 12, padding: 14 }}>
                {sending ? 'Enviando...' : 'Enviar link'}
              </button>
            </form>
          </>
        )}

        <p style={{ textAlign: 'center', marginTop: 24 }}>
          <button className="ghost" onClick={onBack}>Voltar para o login</button>
        </p>
      </div>
    </div>
  )
}

export default ForgotPassword
