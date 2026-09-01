/**
 * Typed API client for the Safeguard backend.
 *
 * All functions:
 *   - automatically attach the Supabase Bearer token
 *   - throw ApiError on non-2xx responses
 *   - throw CompanyNotActiveError on the PENDING/SUSPENDED 403
 *
 * Usage (client components):
 *   import { api } from '@/lib/api'
 *   const buildings = await api.buildings.list(companyId)
 */

import { createSupabaseClient } from './supabase';
import type {
  ApiCompany,
  ApiCompanyMember,
  ApiTrade,
  ApiBuilding,
  ApiBuildingDetail,
  ApiContract,
  ApiAsset,
  ApiJob,
  ApiInspectionResult,
  ApiInspectionResultBody,
  ApiIssue,
  ApiIssueStatus,
  ApiRenewalPack,
  ApiConversation,
  ApiMessage,
  ApiTechnician,
} from './api-types';

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:3000';

// ─── Error classes ────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string | undefined,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/** Thrown when company.status is PENDING or SUSPENDED (backend returns 403). */
export class CompanyNotActiveError extends ApiError {
  constructor() {
    super(403, 'COMPANY_NOT_ACTIVE', "JRHQ hasn't granted this company access yet");
    this.name = 'CompanyNotActiveError';
  }
}

// ─── Core fetch helper ────────────────────────────────────────────────────────

async function getToken(): Promise<string | null> {
  try {
    const supabase = createSupabaseClient();
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  } catch {
    return null;
  }
}

async function apiFetch<T>(
  path: string,
  options?: RequestInit & { token?: string },
): Promise<T> {
  const token = options?.token ?? (await getToken());
  const { token: _omit, ...fetchOptions } = options ?? {};

  const res = await fetch(`${API_URL}${path}`, {
    ...fetchOptions,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...fetchOptions?.headers,
    },
  });

  if (!res.ok) {
    const body: { error?: string; code?: string } = await res
      .json()
      .catch(() => ({}));

    if (
      res.status === 403 &&
      typeof body.error === 'string' &&
      body.error.toLowerCase().includes('jrhq')
    ) {
      throw new CompanyNotActiveError();
    }

    throw new ApiError(
      res.status,
      body.code,
      body.error ?? res.statusText,
    );
  }

  return res.json() as Promise<T>;
}

// ─── Endpoint groups ──────────────────────────────────────────────────────────

const companies = {
  list: () =>
    apiFetch<ApiCompany[]>('/api/companies'),

  create: (body: { name: string; emirate: string; licenceNo?: string }) =>
    apiFetch<ApiCompany>('/api/companies', { method: 'POST', body: JSON.stringify(body) }),

  setStatus: (id: string, status: 'PENDING' | 'ACTIVE' | 'SUSPENDED') =>
    apiFetch<ApiCompany>(`/api/companies/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  members: (id: string) =>
    apiFetch<ApiCompanyMember[]>(`/api/companies/${id}/members`),

  addMember: (id: string, body: { userId: string; role: string }) =>
    apiFetch<ApiCompanyMember>(`/api/companies/${id}/members`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  technicians: (id: string) =>
    apiFetch<ApiTechnician[]>(`/api/companies/${id}/technicians`),

  addTechnician: (id: string, body: { userId: string }) =>
    apiFetch<ApiTechnician>(`/api/companies/${id}/technicians`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  trades: (id: string) =>
    apiFetch<ApiTrade[]>(`/api/companies/${id}/trades`),

  assignTrades: (id: string, tradeIds: string[]) =>
    apiFetch<void>(`/api/companies/${id}/trades`, {
      method: 'POST',
      body: JSON.stringify({ tradeIds }),
    }),
};

const buildings = {
  list: (companyId: string) =>
    apiFetch<ApiBuilding[]>(`/api/buildings?companyId=${companyId}`),

  get: (id: string) =>
    apiFetch<ApiBuildingDetail>(`/api/buildings/${id}`),

  create: (body: {
    companyId: string;
    name: string;
    emirate: string;
    addressLine?: string;
  }) =>
    apiFetch<ApiBuilding>('/api/buildings', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  /** Buildings owned by the currently authenticated user. */
  mine: () =>
    apiFetch<ApiBuilding[]>('/api/owners/buildings'),
};

const contracts = {
  list: (companyId: string) =>
    apiFetch<ApiContract[]>(`/api/contracts?companyId=${companyId}`),

  create: (body: {
    companyId: string;
    buildingId: string;
    tradeId: string;
    startDate: string;
    renewalDate: string;
    slaHours?: number;
  }) =>
    apiFetch<ApiContract>('/api/contracts', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

const assets = {
  list: (buildingId: string) =>
    apiFetch<ApiAsset[]>(`/api/assets?buildingId=${buildingId}`),

  create: (body: { buildingId: string; assetTypeId: string; tag: string }) =>
    apiFetch<ApiAsset>('/api/assets', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

const jobs = {
  /** "Today's jobs" — pass technicianId to filter to one technician. */
  listByTechnician: (technicianId: string) =>
    apiFetch<ApiJob[]>(`/api/jobs?technicianId=${technicianId}`),

  listByBuilding: (buildingId: string) =>
    apiFetch<ApiJob[]>(`/api/jobs?buildingId=${buildingId}`),

  create: (body: { buildingId: string; technicianId: string; scheduledFor: string }) =>
    apiFetch<ApiJob>('/api/jobs', { method: 'POST', body: JSON.stringify(body) }),
};

const inspectionResults = {
  list: (jobId: string) =>
    apiFetch<ApiInspectionResult[]>(`/api/inspection-results?jobId=${jobId}`),

  /**
   * Append-only — no edit endpoint exists. Returns 409 if the same
   * jobId + assetId combination has already been submitted.
   * A FAIL outcome automatically opens an Issue on the backend.
   */
  submit: (body: ApiInspectionResultBody) =>
    apiFetch<ApiInspectionResult>('/api/inspection-results', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

const issues = {
  list: (buildingId: string) =>
    apiFetch<ApiIssue[]>(`/api/issues?buildingId=${buildingId}`),

  /** Owners can view but not close issues — only contracted company can update. */
  updateStatus: (id: string, status: Extract<ApiIssueStatus, 'QUOTED' | 'RESOLVED'>) =>
    apiFetch<ApiIssue>(`/api/issues/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),
};

const renewalPacks = {
  list: (buildingId: string) =>
    apiFetch<ApiRenewalPack[]>(`/api/renewal-packs?buildingId=${buildingId}`),

  create: (body: {
    buildingId: string;
    contractId: string;
    periodStart: string;
    periodEnd: string;
  }) =>
    apiFetch<ApiRenewalPack>('/api/renewal-packs', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

const conversations = {
  list: () =>
    apiFetch<ApiConversation[]>('/api/conversations'),

  messages: (conversationId: string, params?: { limit?: number; before?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.before) qs.set('before', params.before);
    return apiFetch<ApiMessage[]>(
      `/api/conversations/${conversationId}/messages?${qs}`,
    );
  },

  /** New messages arrive via Supabase realtime — use this only to send. */
  send: (conversationId: string, body: { body: string; attachmentUrl?: string }) =>
    apiFetch<ApiMessage>(`/api/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  markRead: (conversationId: string) =>
    apiFetch<void>(`/api/conversations/${conversationId}/read`, { method: 'POST' }),
};

export const api = {
  companies,
  buildings,
  contracts,
  assets,
  jobs,
  inspectionResults,
  issues,
  renewalPacks,
  conversations,
};
