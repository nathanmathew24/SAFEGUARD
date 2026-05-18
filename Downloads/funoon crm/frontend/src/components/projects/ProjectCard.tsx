import { useNavigate } from 'react-router-dom'
import type { Project } from '../../hooks/useProjects'
import { formatDate, formatRelative } from '../../lib/utils'
import { HealthBadge } from './HealthBadge'

export function ProjectCard({ project }: { project: Project }) {
  const navigate = useNavigate()
  return (
    <div
      onClick={() => navigate(`/projects/${project.id}`)}
      className="bg-white border border-ink-100 rounded-lg p-4 cursor-pointer hover:border-ink-200 transition-colors space-y-3"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-ink-800">{project.name}</p>
        <HealthBadge health={project.health} />
      </div>

      {project.stack_tags && project.stack_tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {project.stack_tags.map(tag => (
            <span key={tag} className="text-xs px-1.5 py-0.5 bg-ink-50 text-ink-500 rounded">
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-ink-400">
        <span>{project.live_since ? `Live since ${formatDate(project.live_since)}` : 'Not live'}</span>
        {project.renewal_date && <span>Renews {formatDate(project.renewal_date)}</span>}
      </div>

      <p className="text-xs text-ink-400">{formatRelative(project.updated_at)}</p>
    </div>
  )
}
