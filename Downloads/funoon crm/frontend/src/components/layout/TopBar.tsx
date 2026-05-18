import { useNavigate } from 'react-router-dom'
import { authApi } from '../../lib/api'
import { useAuthStore } from '../../stores/authStore'
import { useUIStore } from '../../stores/uiStore'

interface TopBarProps {
  title: string
  actions?: React.ReactNode
}

export function TopBar({ title, actions }: TopBarProps) {
  const navigate = useNavigate()
  const logout = useAuthStore((s) => s.logout)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)

  async function handleLogout() {
    await authApi.post('/logout').catch(() => null)
    logout()
    navigate('/login')
  }

  return (
    <div className="flex items-center justify-between px-6 py-3 border-b border-ink-100 bg-white sticky top-0 z-10">
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="text-ink-400 hover:text-ink-600 transition-colors text-sm"
          aria-label="Toggle sidebar"
        >
          ☰
        </button>
        <h1 className="text-sm font-medium text-ink-800">{title}</h1>
      </div>
      <div className="flex items-center gap-3">
        {actions}
        <button
          onClick={handleLogout}
          className="text-xs text-ink-400 hover:text-ink-600 transition-colors"
        >
          Sign out
        </button>
      </div>
    </div>
  )
}
