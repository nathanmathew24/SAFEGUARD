import { TopBar } from '../components/layout/TopBar'
import { HealthBadge } from '../components/projects/HealthBadge'
import { EmptyState } from '../components/ui/EmptyState'
import { useMonitoringSummary } from '../hooks/useMonitoring'

export function AIOps() {
  const { data: summaries = [], isLoading } = useMonitoringSummary()

  return (
    <div className="flex flex-col h-full">
      <TopBar title="AI ops" />

      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="text-sm text-ink-400">Loading...</div>
        ) : summaries.length === 0 ? (
          <EmptyState title="No projects being monitored" description="Add a monitoring config to a project to start tracking ops health." />
        ) : (
          <div className="border border-ink-100 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-ink-50">
                <tr>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">Project</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">Health</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">Uptime 24h</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">Error rate 24h</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">Token spend</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">Last alert</th>
                </tr>
              </thead>
              <tbody>
                {summaries.map(s => (
                  <tr key={s.project_id} className="border-t border-ink-100 hover:bg-ink-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-ink-800">{s.project_name}</td>
                    <td className="px-4 py-3">
                      <HealthBadge health={s.health as 'green' | 'amber' | 'red'} />
                    </td>
                    <td className="px-4 py-3 text-ink-600">
                      {s.metrics.uptime_24h != null ? `${s.metrics.uptime_24h.toFixed(1)}%` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      {s.metrics.error_rate_24h != null ? (
                        <span className={s.metrics.error_rate_24h > 5 ? 'text-status-red font-medium' : 'text-ink-600'}>
                          {s.metrics.error_rate_24h.toFixed(1)}%
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-ink-600">
                      {s.metrics.token_spend_day != null ? `$${s.metrics.token_spend_day.toFixed(2)}` : '—'}
                    </td>
                    <td className="px-4 py-3 text-ink-500 text-xs max-w-[200px] truncate">
                      {s.last_alert ? (
                        <span title={s.last_alert}>{s.last_alert}</span>
                      ) : <span className="text-ink-300">None</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
