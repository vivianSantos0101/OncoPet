import { LogOut } from 'lucide-react'
import { LogoMark } from './Logo'

const ROLE_LABEL = { vet: 'Veterinario', tutor: 'Tutor' }

function AppHeader({ role, userName, onLogout }) {
  return (
    <div className="header">
      <h1><LogoMark size={36} title="" />OncoPet</h1>
      <div className="header-user">
        <span className={`role-badge ${role}`}>{ROLE_LABEL[role]}</span>
        <span className="user-name">{userName}</span>
        <button className="danger icon-btn" onClick={onLogout} aria-label="Sair" title="Sair">
          <LogOut size={16} />
          <span className="btn-label">Sair</span>
        </button>
      </div>
    </div>
  )
}

export default AppHeader
