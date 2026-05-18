import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export interface Client {
  id: string
  name: string
  contact_name: string | null
  whatsapp: string | null
  email: string | null
  source: string | null
  stage: string
  enquiry: string | null
  estimated_mrr: number | null
  next_action: string | null
  next_action_due: string | null
  ai_context: string | null
  ai_context_updated_at: string | null
  created_at: string
  updated_at: string
}

export interface ClientNote {
  id: string
  body: string
  created_at: string
}

export interface StageHistory {
  id: string
  from_stage: string | null
  to_stage: string
  note: string | null
  moved_at: string
}

export interface ClientDetail extends Client {
  notes: ClientNote[]
  stage_history: StageHistory[]
}

export function useClients(stage?: string) {
  return useQuery({
    queryKey: ['clients', stage],
    queryFn: async () => {
      const res = await api.get<Client[]>('/clients', { params: stage ? { stage } : {} })
      return res.data
    },
  })
}

export function useClient(id: string) {
  return useQuery({
    queryKey: ['clients', id],
    queryFn: async () => {
      const res = await api.get<ClientDetail>(`/clients/${id}`)
      return res.data
    },
    enabled: !!id,
  })
}

export function useCreateClient() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Client>) => api.post<Client>('/clients', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clients'] }),
  })
}

export function useUpdateClient(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Client>) => api.patch<Client>(`/clients/${id}`, data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clients'] }),
  })
}

export function useMoveStage(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { to_stage: string; note?: string }) =>
      api.post<Client>(`/clients/${id}/stage`, data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clients'] }),
  })
}

export function useAddNote(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: string) =>
      api.post<ClientNote>(`/clients/${id}/notes`, { body }).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clients', id] }),
  })
}

export function useAISummarise(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<{ summary: string }>(`/clients/${id}/ai/summarise`).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clients', id] }),
  })
}

export function useAIFollowup(id: string) {
  return useMutation({
    mutationFn: () => api.post<{ message: string }>(`/clients/${id}/ai/followup`).then(r => r.data),
  })
}
