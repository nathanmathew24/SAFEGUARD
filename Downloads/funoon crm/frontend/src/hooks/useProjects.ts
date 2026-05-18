import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export interface Blocker {
  id: string
  body: string
  owner: string | null
  due_date: string | null
  resolved: boolean
  resolved_at: string | null
  created_at: string
}

export interface ProjectNote {
  id: string
  body: string
  created_at: string
}

export interface Project {
  id: string
  client_id: string | null
  name: string
  health: 'green' | 'amber' | 'red'
  live_since: string | null
  renewal_date: string | null
  stack_tags: string[] | null
  external_links: Record<string, string> | null
  created_at: string
  updated_at: string
}

export interface ProjectDetail extends Project {
  blockers: Blocker[]
  notes: ProjectNote[]
}

export function useProjects(health?: string) {
  return useQuery({
    queryKey: ['projects', health],
    queryFn: async () => {
      const res = await api.get<Project[]>('/projects', { params: health ? { health } : {} })
      return res.data
    },
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: async () => {
      const res = await api.get<ProjectDetail>(`/projects/${id}`)
      return res.data
    },
    enabled: !!id,
  })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Project>) => api.post<Project>('/projects', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useUpdateProject(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Project>) => api.patch<Project>(`/projects/${id}`, data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })
}

export function useAddBlocker(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { body: string; owner?: string; due_date?: string }) =>
      api.post<Blocker>(`/projects/${projectId}/blockers`, data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects', projectId] }),
  })
}

export function useResolveBlocker(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (blockerId: string) =>
      api.patch<Blocker>(`/projects/${projectId}/blockers/${blockerId}/resolve`).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects', projectId] }),
  })
}

export function useAddProjectNote(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: string) =>
      api.post<ProjectNote>(`/projects/${projectId}/notes`, { body }).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects', projectId] }),
  })
}

export function useProjectAISummarise(id: string) {
  return useMutation({
    mutationFn: () => api.post<{ summary: string }>(`/projects/${id}/ai/summarise`).then(r => r.data),
  })
}

export function useProjectAIClientUpdate(id: string) {
  return useMutation({
    mutationFn: () => api.post<{ message: string }>(`/projects/${id}/ai/client-update`).then(r => r.data),
  })
}
