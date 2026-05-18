import { NavLink } from 'react-router-dom'
import { cn } from '../../lib/utils'
import { useUIStore } from '../../stores/uiStore'

const NAV = [
  { to: '/pipeline',  label: 'Pipeline' },
  { to: '/projects',  label: 'Projects' },
  { to: '/ai-ops',    label: 'AI ops' },
  { to: '/financial', label: 'Financial' },
  { to: '/library',   label: 'Library' },
  { to: '/workspace', label: 'Workspace' },
]

export function Sidebar() {
  const collapsed = useUIStore((s) => s.sidebarCollapsed)

  return (
    <aside
      className={cn(
        'flex flex-col bg-white border-r border-ink-100 h-screen sticky top-0 transition-all',
        collapsed ? 'w-12' : 'w-48',
      )}
    >
      {/* Wordmark */}
      <div className="px-4 py-4 border-b border-ink-100">
        {collapsed ? (
          <span className="text-sm font-medium text-ink-900">f</span>
        ) : (
          <div>
            <span className="text-sm font-medium text-ink-900 tracking-tight">funoon</span>
            <span className="ml-1 text-xs text-ink-400">crm</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 space-y-0.5 px-2">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'flex items-center px-2 py-1.5 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-ink-100 text-ink-800 font-medium'
                  : 'text-ink-500 hover:bg-ink-50 hover:text-ink-700',
              )
            }
          >
            {!collapsed && item.label}
            {collapsed && (
              <span className="text-xs font-medium">{item.label[0]}</span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-2 pb-3 border-t border-ink-100 pt-2 space-y-0.5">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn(
              'flex items-center px-2 py-1.5 rounded-md text-sm transition-colors',
              isActive
                ? 'bg-ink-100 text-ink-800 font-medium'
                : 'text-ink-500 hover:bg-ink-50 hover:text-ink-700',
            )
          }
        >
          {collapsed ? 'S' : 'Settings'}
        </NavLink>
      </div>
    </aside>
  )
}
