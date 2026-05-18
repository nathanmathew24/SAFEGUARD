import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export interface MonitoringSummary {
  project_id: string
  project_name: string
  health: string
  metrics: Record<string, number>
  last_alert: string | null
  last_alert_at: string | null
}

export interface MonitoringEvent {
  id: string
  project_id: string
  event_type: string
  severity: string
  description: string | null
  resolved: boolean
  resolved_at: string | null
  occurred_at: string
}

export function useMonitoringSummary() {
  return useQuery({
    queryKey: ['monitoring'],
    queryFn: () => api.get<MonitoringSummary[]>('/monitoring').then(r => r.data),
    refetchInterval: 60_000,
  })
}

export function useMonitoringEvents(projectId: string) {
  return useQuery({
    queryKey: ['monitoring', projectId, 'events'],
    queryFn: () => api.get<MonitoringEvent[]>(`/monitoring/${projectId}/events`).then(r => r.data),
    enabled: !!projectId,
  })
}

export function useResolveEvent(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (eventId: string) =>
      api.patch(`/monitoring/${projectId}/events/${eventId}/resolve`).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['monitoring'] }),
  })
}
