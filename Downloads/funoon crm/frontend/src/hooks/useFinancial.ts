import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export interface LineItem { description: string; qty: number; unit_price: number }

export interface FinancialSummary {
  mrr: number
  arr: number
  infra_cost_month: number
  expense_total_month: number
  total_cost_month: number
  net_margin_month: number
  revenue_at_risk: number
  revenue_collected_month: number
}

export interface PLRow {
  month: string
  revenue: number
  infra_cost: number
  expenses: number
  total_cost: number
  net: number
}

export interface Invoice {
  id: string
  client_id: string | null
  client_name?: string | null
  number: string | null
  amount: number
  issued_date: string | null
  due_date: string | null
  paid_date?: string | null
  status: string
  notes: string | null
  doc_type?: string
  line_items?: LineItem[] | null
}

export interface BillingRecord {
  id: string
  client_id: string
  client_name?: string | null
  amount: number
  cycle: string
  status: string
  started_at: string | null
  ended_at: string | null
  notes: string | null
}

export interface InfraCost {
  id: string
  project_id: string | null
  service: string
  amount: number
  month: string
  notes: string | null
}

export interface Expense {
  id: string
  category: string
  description: string
  amount: number
  month: string
  recurring: boolean
  notes: string | null
  created_at: string
}

export interface ProjectMargin {
  project_id: string
  project_name: string
  mrr: number
  infra_cost: number
  margin: number
  margin_pct: number
}

export function useFinancialSummary() {
  return useQuery({
    queryKey: ['financial', 'summary'],
    queryFn: () => api.get<FinancialSummary>('/financial/summary').then(r => r.data),
  })
}

export function usePLSummary(months = 6) {
  return useQuery({
    queryKey: ['financial', 'pl', months],
    queryFn: () => api.get<{ rows: PLRow[] }>('/financial/pl', { params: { months } }).then(r => r.data),
  })
}

export function useProjectMargins() {
  return useQuery({
    queryKey: ['financial', 'margins'],
    queryFn: () => api.get<ProjectMargin[]>('/financial/project-margins').then(r => r.data),
  })
}

export function useInvoices() {
  return useQuery({
    queryKey: ['financial', 'invoices'],
    queryFn: () => api.get<Invoice[]>('/financial/invoices').then(r => r.data),
  })
}

export function useCreateInvoice() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Invoice>) => api.post<Invoice>('/financial/invoices', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial'] }),
  })
}

export function useUpdateInvoice() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Invoice> }) =>
      api.patch<Invoice>(`/financial/invoices/${id}`, data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial'] }),
  })
}

export function useDeleteInvoice() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/financial/invoices/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial'] }),
  })
}

export function useBillingRecords() {
  return useQuery({
    queryKey: ['financial', 'billing'],
    queryFn: () => api.get<BillingRecord[]>('/financial/billing').then(r => r.data),
  })
}

export function useCreateBilling() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<BillingRecord>) => api.post<BillingRecord>('/financial/billing', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial'] }),
  })
}

export function useUpdateBilling() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<BillingRecord> }) =>
      api.patch<BillingRecord>(`/financial/billing/${id}`, data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial'] }),
  })
}

export function useDeleteBilling() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/financial/billing/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial'] }),
  })
}

export function useInfraCosts(month?: string) {
  return useQuery({
    queryKey: ['financial', 'infra', month],
    queryFn: () => api.get<InfraCost[]>('/financial/infra', { params: month ? { month } : {} }).then(r => r.data),
  })
}

export function useCreateInfraCost() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<InfraCost>) => api.post<InfraCost>('/financial/infra', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial'] }),
  })
}

export function useDeleteInfraCost() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/financial/infra/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial'] }),
  })
}

export function useExpenses(month?: string) {
  return useQuery({
    queryKey: ['financial', 'expenses', month],
    queryFn: () => api.get<Expense[]>('/financial/expenses', { params: month ? { month } : {} }).then(r => r.data),
  })
}

export function useCreateExpense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Expense>) => api.post<Expense>('/financial/expenses', data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial'] }),
  })
}

export function useDeleteExpense() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/financial/expenses/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['financial'] }),
  })
}
