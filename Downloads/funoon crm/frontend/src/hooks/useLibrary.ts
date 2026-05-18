import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export interface Component {
  id: string
  name: string
  category: string
  description: string | null
  tech_tags: string[] | null
  status: string
  version: string | null
  github_path: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export function useComponents(params?: { category?: string; status_filter?: string; q?: string }) {
  return useQuery({
    queryKey: ['library', params],
    queryFn: () => api.get<Component[]>('/library', { params }).then(r => r.data),
  })
}

export function useCreateComponent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Component>) => api.post<Component>('/library', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['library'] }),
  })
}

export function useUpdateComponent(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Component>) => api.patch<Component>(`/library/${id}`, data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['library'] }),
  })
}

export function useAISuggestComponents() {
  return useMutation({
    mutationFn: (description: string) =>
      api.post<{ suggestion: string }>('/library/ai/suggest', { description }).then(r => r.data),
  })
}
