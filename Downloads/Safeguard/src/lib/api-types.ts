/**
 * Wire types — these match what the backend API actually returns.
 * They are NOT the same as the UI types in types.ts:
 *   - outcome is 'PASS' | 'FAIL' (uppercase), not a boolean
 *   - issue status uses 'OPEN' | 'QUOTED' | 'RESOLVED' (not 'open' | 'in-progress' | 'resolved')
 *   - jobs have a single scheduledFor ISO datetime, not scheduledDate + scheduledTime
 *   - trade ids are UUIDs, not slugs ('fire' | 'hvac' | 'elv')
 *
 * When connecting a page to the real API, map these types to the UI types in types.ts.
 */

// ─── Auth / session ───────────────────────────────────────────────────────────

export type CompanyStatus = 'PENDING' | 'ACTIVE' | 'SUSPENDED';

// ─── Companies ────────────────────────────────────────────────────────────────

export interface ApiCompany {
  id: string;
  name: string;
  emirate: string;
  licenceNo: string | null;
  status: CompanyStatus;
}

export interface ApiCompanyMember {
  id: string;
  userId: string;
  companyId: string;
  role: 'OWNER_ADMIN' | 'COORDINATOR' | 'TECHNICIAN';
}

// ─── Trades ───────────────────────────────────────────────────────────────────
// Note: backend trade ids are UUIDs, not 'fire' | 'hvac' | 'elv' slugs.
// GET /api/companies/:id/trades returns only trades assigned to that company.
// There is no endpoint yet that returns the full trade catalog.

export interface ApiTrade {
  id: string; // UUID
  name: string; // e.g. "Fire Safety", "HVAC", "ELV"
}

// ─── Buildings ────────────────────────────────────────────────────────────────

export interface ApiBuilding {
  id: string;
  name: string;
  emirate: string;
  addressLine: string | null;
}

// GET /api/buildings/:id returns the full detail shape below
export interface ApiBuildingDetail extends ApiBuilding {
  contracts: ApiContract[];
  assets: ApiAsset[];
  openIssues: ApiIssue[];
  recentRenewalPacks: ApiRenewalPack[];
}

// ─── Contracts ────────────────────────────────────────────────────────────────

export interface ApiContract {
  id: string;
  companyId: string;
  buildingId: string;
  tradeId: string; // UUID
  startDate: string; // ISO date
  renewalDate: string; // ISO date
  slaHours: number | null;
}

// ─── Assets ───────────────────────────────────────────────────────────────────

export interface ApiAsset {
  id: string;
  buildingId: string;
  assetTypeId: string; // UUID — no full catalog endpoint yet
  tag: string;
}

// ─── Jobs ─────────────────────────────────────────────────────────────────────
// The backend calls these "jobs"; the frontend UI calls them "visits".
// scheduledFor is a single ISO datetime (not split into date + time).

export interface ApiJob {
  id: string;
  buildingId: string;
  technicianId: string;
  scheduledFor: string; // ISO datetime, e.g. "2026-09-01T09:00:00.000Z"
}

// ─── Inspection results ───────────────────────────────────────────────────────
// Append-only: no PATCH/PUT endpoint exists.
// A second POST for the same jobId + assetId returns 409.
// A FAIL outcome auto-opens an Issue.

export type InspectionOutcome = 'PASS' | 'FAIL';

export interface ApiEvidence {
  photoUrl: string;
  deviceId: string | null;
  capturedAt: string; // ISO datetime
}

export interface ApiInspectionResult {
  id: string;
  jobId: string;
  assetId: string;
  outcome: InspectionOutcome;
  notes: string | null;
  recordedAt: string; // ISO datetime
  evidence: ApiEvidence[];
}

// POST body
export interface ApiInspectionResultBody {
  jobId: string;
  assetId: string;
  outcome: InspectionOutcome;
  notes?: string;
  recordedAt: string;
  evidence: Array<{
    photoUrl: string;
    deviceId?: string;
    capturedAt: string;
  }>;
}

// ─── Issues ───────────────────────────────────────────────────────────────────
// OPEN → QUOTED → RESOLVED (owners can view but not close an issue)

export type ApiIssueStatus = 'OPEN' | 'QUOTED' | 'RESOLVED';

export interface ApiIssue {
  id: string;
  status: ApiIssueStatus;
  buildingId: string;
  assetId: string | null;
  // auto-opened from a FAIL result
}

// ─── Renewal packs ────────────────────────────────────────────────────────────
// fileUrl is always null — PDF generation is not built yet.

export interface ApiRenewalPack {
  id: string;
  buildingId: string;
  contractId: string;
  periodStart: string; // ISO date
  periodEnd: string; // ISO date
  fileUrl: null;
}

// ─── Chat ─────────────────────────────────────────────────────────────────────
// New messages arrive via Supabase realtime subscription, not polling.
// See the handoff doc for the subscription snippet.

export interface ApiConversation {
  id: string;
  lastMessage: string | null;
  unreadCount: number;
}

export interface ApiMessage {
  id: string;
  conversationId: string;
  body: string;
  attachmentUrl: string | null;
  createdAt: string; // ISO datetime
  senderId: string;
}

// ─── Technicians ─────────────────────────────────────────────────────────────

export interface ApiTechnician {
  id: string;
  userId: string;
  companyId: string;
}

// ─── API error shape ─────────────────────────────────────────────────────────

export interface ApiErrorBody {
  error: string;
  code?: string;
}
