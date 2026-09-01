import type {
  Building, Asset, Technician, Visit, AssetResult,
  Issue, Report, InspectionRule, Trade
} from './types';

// ─── Trade lookup ─────────────────────────────────────────────────────────────
export const TRADES: Trade[] = [
  { id: 'fire', label: 'Fire Safety', description: 'Fire suppression, detection & egress systems' },
  { id: 'hvac', label: 'HVAC', description: 'Heating, ventilation & air conditioning systems' },
  { id: 'elv', label: 'ELV', description: 'Extra low voltage: CCTV, access control, BMS, intercom' },
];

// ─── Technicians ──────────────────────────────────────────────────────────────
export const technicians: Technician[] = [
  {
    id: 'tech-001',
    name: 'Ahmed Al Mansoori',
    initials: 'AM',
    trades: ['fire', 'hvac'],
    phone: '+971 50 234 5678',
    email: 'ahmed.m@emiratessafety.ae',
    activeJobCount: 3,
  },
  {
    id: 'tech-002',
    name: 'Sara Khalil',
    initials: 'SK',
    trades: ['hvac', 'elv'],
    phone: '+971 55 876 4321',
    email: 'sara.k@emiratessafety.ae',
    activeJobCount: 2,
  },
];

// ─── Buildings ────────────────────────────────────────────────────────────────
export const buildings: Building[] = [
  {
    id: 'bld-001',
    name: 'Al Quoz Industrial Centre',
    address: 'Al Quoz Industrial Area 1, Street 8, Dubai',
    emirate: 'Dubai',
    health: 'warning',
    tradeHealth: { fire: 'critical', hvac: 'ok', elv: 'warning' },
    trades: ['fire', 'hvac', 'elv'],
    assignedTechnicianIds: ['tech-001', 'tech-002'],
    ownerContact: { name: 'Majid Al Rashidi', phone: '+971 4 345 6789', email: 'majid@alquozindustrial.ae' },
    assetCount: 5,
    nextInspection: '2026-09-08',
    lastInspection: '2026-07-15',
  },
  {
    id: 'bld-002',
    name: 'Sharjah Expo Business Centre',
    address: 'Al Taawun, Sharjah Expo Centre Road, Sharjah',
    emirate: 'Sharjah',
    health: 'ok',
    tradeHealth: { fire: 'ok', hvac: null, elv: 'ok' },
    trades: ['fire', 'elv'],
    assignedTechnicianIds: ['tech-001'],
    ownerContact: { name: 'Hessa Al Nuaimi', phone: '+971 6 522 1100', email: 'hessa@sharjahexpo.ae' },
    assetCount: 3,
    nextInspection: '2026-09-20',
    lastInspection: '2026-08-10',
  },
  {
    id: 'bld-003',
    name: 'Al Reem Tower',
    address: 'Al Reem Island, Abu Dhabi',
    emirate: 'Abu Dhabi',
    health: 'ok',
    tradeHealth: { fire: 'ok', hvac: 'ok', elv: null },
    trades: ['fire', 'hvac'],
    assignedTechnicianIds: ['tech-001', 'tech-002'],
    ownerContact: { name: 'Khalid Al Falasi', phone: '+971 2 671 9000', email: 'k.falasi@reemtower.ae' },
    assetCount: 4,
    nextInspection: '2026-10-01',
    lastInspection: '2026-08-20',
  },
  {
    id: 'bld-004',
    name: 'Marina Gate Residences',
    address: 'Dubai Marina, Gate Avenue, Dubai',
    emirate: 'Dubai',
    health: 'warning',
    tradeHealth: { fire: null, hvac: 'warning', elv: 'ok' },
    trades: ['hvac', 'elv'],
    assignedTechnicianIds: ['tech-002'],
    ownerContact: { name: 'Nadia Saleh', phone: '+971 4 888 2200', email: 'nadia.s@marinagate.ae' },
    assetCount: 3,
    nextInspection: '2026-09-12',
    lastInspection: '2026-07-28',
  },
];

// ─── Assets ───────────────────────────────────────────────────────────────────
export const assets: Asset[] = [
  // Fire — Al Quoz
  {
    id: 'ast-001', tag: 'EX-014', buildingId: 'bld-001', trade: 'fire',
    type: 'Fire Extinguisher', status: 'fail', lastChecked: '2026-07-15', nextDue: '2026-09-08',
    photoHistory: [],
  },
  {
    id: 'ast-002', tag: 'HD-03', buildingId: 'bld-001', trade: 'fire',
    type: 'Heat Detector', status: 'pass', lastChecked: '2026-07-15', nextDue: '2026-09-08',
    photoHistory: [],
  },
  // HVAC — Al Quoz
  {
    id: 'ast-003', tag: 'AHU-03', buildingId: 'bld-001', trade: 'hvac',
    type: 'Air Handling Unit', status: 'pass', lastChecked: '2026-08-01', nextDue: '2026-10-01',
    photoHistory: [],
  },
  // ELV — Al Quoz
  {
    id: 'ast-004', tag: 'CAM-07', buildingId: 'bld-001', trade: 'elv',
    type: 'IP Camera', status: 'pending', lastChecked: '2026-06-20', nextDue: '2026-09-10',
    photoHistory: [],
  },
  {
    id: 'ast-005', tag: 'ACP-02', buildingId: 'bld-001', trade: 'elv',
    type: 'Access Control Panel', status: 'pass', lastChecked: '2026-06-20', nextDue: '2026-09-10',
    photoHistory: [],
  },
  // Fire — Sharjah Expo
  {
    id: 'ast-006', tag: 'EX-015', buildingId: 'bld-002', trade: 'fire',
    type: 'Fire Extinguisher', status: 'pass', lastChecked: '2026-08-10', nextDue: '2026-10-10',
    photoHistory: [],
  },
  // ELV — Sharjah Expo
  {
    id: 'ast-007', tag: 'CAM-08', buildingId: 'bld-002', trade: 'elv',
    type: 'IP Camera', status: 'pass', lastChecked: '2026-08-10', nextDue: '2026-11-10',
    photoHistory: [],
  },
  // Fire — Al Reem Tower
  {
    id: 'ast-008', tag: 'HR-022', buildingId: 'bld-003', trade: 'fire',
    type: 'Hose Reel', status: 'pass', lastChecked: '2026-08-20', nextDue: '2026-11-20',
    photoHistory: [],
  },
  // HVAC — Al Reem Tower
  {
    id: 'ast-009', tag: 'AHU-07', buildingId: 'bld-003', trade: 'hvac',
    type: 'Air Handling Unit', status: 'pass', lastChecked: '2026-08-20', nextDue: '2026-10-20',
    photoHistory: [],
  },
  {
    id: 'ast-010', tag: 'FCU-11', buildingId: 'bld-003', trade: 'hvac',
    type: 'Fan Coil Unit', status: 'pass', lastChecked: '2026-08-20', nextDue: '2026-10-20',
    photoHistory: [],
  },
  // HVAC — Marina Gate
  {
    id: 'ast-011', tag: 'AHU-09', buildingId: 'bld-004', trade: 'hvac',
    type: 'Air Handling Unit', status: 'expired', lastChecked: '2026-06-01', nextDue: '2026-08-01',
    photoHistory: [],
  },
  // ELV — Marina Gate
  {
    id: 'ast-012', tag: 'BMS-01', buildingId: 'bld-004', trade: 'elv',
    type: 'BMS Gateway', status: 'pass', lastChecked: '2026-07-28', nextDue: '2026-10-28',
    photoHistory: [],
  },
];

// ─── Visits ───────────────────────────────────────────────────────────────────
export const visits: Visit[] = [
  // Completed visits
  {
    id: 'vis-001', buildingId: 'bld-001', technicianId: 'tech-001', trade: 'fire',
    scheduledDate: '2026-07-15', scheduledTime: '09:00',
    status: 'completed', assetIds: ['ast-001', 'ast-002'], completedAt: '2026-07-15T11:30:00Z',
  },
  {
    id: 'vis-002', buildingId: 'bld-002', technicianId: 'tech-001', trade: 'fire',
    scheduledDate: '2026-08-10', scheduledTime: '10:00',
    status: 'completed', assetIds: ['ast-006', 'ast-007'], completedAt: '2026-08-10T12:00:00Z',
  },
  {
    id: 'vis-003', buildingId: 'bld-003', technicianId: 'tech-002', trade: 'hvac',
    scheduledDate: '2026-08-20', scheduledTime: '08:00',
    status: 'completed', assetIds: ['ast-009', 'ast-010'], completedAt: '2026-08-20T10:45:00Z',
  },
  // Today's jobs (2026-09-01)
  {
    id: 'vis-004', buildingId: 'bld-001', technicianId: 'tech-001', trade: 'hvac',
    scheduledDate: '2026-09-01', scheduledTime: '09:00',
    status: 'in-progress', assetIds: ['ast-003'],
  },
  {
    id: 'vis-005', buildingId: 'bld-004', technicianId: 'tech-002', trade: 'elv',
    scheduledDate: '2026-09-01', scheduledTime: '11:00',
    status: 'scheduled', assetIds: ['ast-012'],
  },
  {
    id: 'vis-006', buildingId: 'bld-001', technicianId: 'tech-001', trade: 'fire',
    scheduledDate: '2026-09-01', scheduledTime: '14:00',
    status: 'scheduled', assetIds: ['ast-001', 'ast-002'],
  },
  // Overdue
  {
    id: 'vis-007', buildingId: 'bld-004', technicianId: 'tech-002', trade: 'hvac',
    scheduledDate: '2026-08-15', scheduledTime: '09:00',
    status: 'overdue', assetIds: ['ast-011'],
  },
  // Upcoming scheduled
  {
    id: 'vis-008', buildingId: 'bld-001', technicianId: 'tech-002', trade: 'elv',
    scheduledDate: '2026-09-08', scheduledTime: '10:00',
    status: 'scheduled', assetIds: ['ast-004', 'ast-005'],
  },
  {
    id: 'vis-009', buildingId: 'bld-002', technicianId: 'tech-001', trade: 'elv',
    scheduledDate: '2026-09-20', scheduledTime: '09:00',
    status: 'scheduled', assetIds: ['ast-007'],
  },
  {
    id: 'vis-010', buildingId: 'bld-003', technicianId: 'tech-001', trade: 'fire',
    scheduledDate: '2026-10-01', scheduledTime: '08:00',
    status: 'scheduled', assetIds: ['ast-008'],
  },
];

// ─── Asset Results ─────────────────────────────────────────────────────────────
export const assetResults: AssetResult[] = [
  // vis-001 results — EX-014 FAILED (this is the cross-portal consistency anchor)
  {
    id: 'res-001', visitId: 'vis-001', assetId: 'ast-001',
    pass: false, photo: '/placeholder-photo.jpg',
    timestamp: '2026-07-15T10:15:00Z', technicianId: 'tech-001',
    deviceMeta: 'Samsung Galaxy A54 · Android 14', synced: true,
  },
  {
    id: 'res-002', visitId: 'vis-001', assetId: 'ast-002',
    pass: true, timestamp: '2026-07-15T10:30:00Z', technicianId: 'tech-001',
    deviceMeta: 'Samsung Galaxy A54 · Android 14', synced: true,
  },
  // vis-002 results
  {
    id: 'res-003', visitId: 'vis-002', assetId: 'ast-006',
    pass: true, timestamp: '2026-08-10T11:00:00Z', technicianId: 'tech-001',
    deviceMeta: 'Samsung Galaxy A54 · Android 14', synced: true,
  },
  {
    id: 'res-004', visitId: 'vis-002', assetId: 'ast-007',
    pass: true, timestamp: '2026-08-10T11:20:00Z', technicianId: 'tech-001',
    deviceMeta: 'Samsung Galaxy A54 · Android 14', synced: true,
  },
  // vis-003 results
  {
    id: 'res-005', visitId: 'vis-003', assetId: 'ast-009',
    pass: true, timestamp: '2026-08-20T09:00:00Z', technicianId: 'tech-002',
    deviceMeta: 'iPhone 15 Pro · iOS 17', synced: true,
  },
  {
    id: 'res-006', visitId: 'vis-003', assetId: 'ast-010',
    pass: true, timestamp: '2026-08-20T09:20:00Z', technicianId: 'tech-002',
    deviceMeta: 'iPhone 15 Pro · iOS 17', synced: true,
  },
  // vis-004 in-progress — local queue (not yet synced)
  {
    id: 'res-007', visitId: 'vis-004', assetId: 'ast-003',
    pass: true, timestamp: '2026-09-01T09:35:00Z', technicianId: 'tech-001',
    deviceMeta: 'Samsung Galaxy A54 · Android 14', synced: false,
  },
];

// ─── Issues ───────────────────────────────────────────────────────────────────
export const issues: Issue[] = [
  {
    id: 'iss-001', assetId: 'ast-001', buildingId: 'bld-001', trade: 'fire',
    type: 'failed-asset', priority: 'high', status: 'open',
    assignedToId: 'tech-001', createdAt: '2026-07-15T12:00:00Z',
    description: 'EX-014 fire extinguisher failed inspection — pressure below minimum threshold. Replacement required.',
  },
  {
    id: 'iss-002', assetId: 'ast-011', buildingId: 'bld-004', trade: 'hvac',
    type: 'expired-cert', priority: 'high', status: 'open',
    createdAt: '2026-08-02T08:00:00Z',
    description: 'AHU-09 service certificate expired on 2026-08-01. Overdue inspection visit.',
  },
  {
    id: 'iss-003', assetId: 'ast-004', buildingId: 'bld-001', trade: 'elv',
    type: 'overdue-inspection', priority: 'medium', status: 'in-progress',
    assignedToId: 'tech-002', createdAt: '2026-08-25T10:00:00Z',
    description: 'CAM-07 inspection overdue by 15 days — visit scheduled for 2026-09-08.',
  },
  {
    id: 'iss-004', assetId: 'ast-007', buildingId: 'bld-004', trade: 'hvac',
    type: 'overdue-inspection', priority: 'medium', status: 'open',
    createdAt: '2026-08-15T09:00:00Z',
    description: 'HVAC quarterly inspection at Marina Gate overdue. Originally scheduled 2026-08-15.',
  },
];

// ─── Reports ──────────────────────────────────────────────────────────────────
export const reports: Report[] = [
  {
    id: 'rpt-001', buildingId: 'bld-001', trades: ['fire'],
    dateRange: { from: '2026-04-01', to: '2026-07-31' },
    generatedAt: '2026-08-01T10:00:00Z',
    documentUrl: '/reports/bld-001-fire-q2.pdf',
    title: 'Al Quoz Industrial Centre — Fire Safety Q2 2026',
  },
  {
    id: 'rpt-002', buildingId: 'bld-002', trades: ['fire', 'elv'],
    dateRange: { from: '2026-05-01', to: '2026-08-31' },
    generatedAt: '2026-08-12T14:00:00Z',
    documentUrl: '/reports/bld-002-fire-elv-q2.pdf',
    title: 'Sharjah Expo Business Centre — Fire & ELV Renewal Pack Q2 2026',
  },
  {
    id: 'rpt-003', buildingId: 'bld-003', trades: ['fire', 'hvac'],
    dateRange: { from: '2026-06-01', to: '2026-08-31' },
    generatedAt: '2026-08-22T09:00:00Z',
    documentUrl: '/reports/bld-003-full-q2.pdf',
    title: 'Al Reem Tower — Fire & HVAC Compliance Report Q2 2026',
  },
];

// ─── Inspection Rules ─────────────────────────────────────────────────────────
export const inspectionRules: InspectionRule[] = [
  // Dubai × Fire
  { id: 'rule-001', emirate: 'Dubai', trade: 'fire', assetType: 'Fire Extinguisher', frequencyDays: 90, standard: 'DCD / NFPA 10' },
  { id: 'rule-002', emirate: 'Dubai', trade: 'fire', assetType: 'Heat Detector', frequencyDays: 365, standard: 'DCD / NFPA 72' },
  { id: 'rule-003', emirate: 'Dubai', trade: 'fire', assetType: 'Hose Reel', frequencyDays: 90, standard: 'DCD / BS 5306' },
  // Dubai × HVAC
  { id: 'rule-004', emirate: 'Dubai', trade: 'hvac', assetType: 'Air Handling Unit', frequencyDays: 90, standard: 'DM / ASHRAE 180' },
  { id: 'rule-005', emirate: 'Dubai', trade: 'hvac', assetType: 'Fan Coil Unit', frequencyDays: 90, standard: 'DM / ASHRAE 180' },
  // Dubai × ELV
  { id: 'rule-006', emirate: 'Dubai', trade: 'elv', assetType: 'IP Camera', frequencyDays: 90, standard: 'DEWA / IEC 62676' },
  { id: 'rule-007', emirate: 'Dubai', trade: 'elv', assetType: 'Access Control Panel', frequencyDays: 180, standard: 'DEWA / EN 50133' },
  { id: 'rule-008', emirate: 'Dubai', trade: 'elv', assetType: 'BMS Gateway', frequencyDays: 180, standard: 'DEWA / EN 15232' },
  // Sharjah × Fire
  { id: 'rule-009', emirate: 'Sharjah', trade: 'fire', assetType: 'Fire Extinguisher', frequencyDays: 90, standard: 'SFCD / NFPA 10' },
  { id: 'rule-010', emirate: 'Sharjah', trade: 'elv', assetType: 'IP Camera', frequencyDays: 120, standard: 'SFCD / IEC 62676' },
  // Abu Dhabi × Fire
  { id: 'rule-011', emirate: 'Abu Dhabi', trade: 'fire', assetType: 'Fire Extinguisher', frequencyDays: 90, standard: 'OSHAD / NFPA 10' },
  { id: 'rule-012', emirate: 'Abu Dhabi', trade: 'fire', assetType: 'Hose Reel', frequencyDays: 90, standard: 'OSHAD / BS 5306' },
  { id: 'rule-013', emirate: 'Abu Dhabi', trade: 'hvac', assetType: 'Air Handling Unit', frequencyDays: 90, standard: 'OSHAD / ASHRAE 180' },
  { id: 'rule-014', emirate: 'Abu Dhabi', trade: 'hvac', assetType: 'Fan Coil Unit', frequencyDays: 90, standard: 'OSHAD / ASHRAE 180' },
];

// ─── Convenience lookups ──────────────────────────────────────────────────────
export const mockData = {
  trades: TRADES,
  buildings,
  assets,
  technicians,
  visits,
  assetResults,
  issues,
  reports,
  inspectionRules,
};

export function getBuildingById(id: string) { return buildings.find(b => b.id === id); }
export function getAssetById(id: string) { return assets.find(a => a.id === id); }
export function getTechnicianById(id: string) { return technicians.find(t => t.id === id); }
export function getVisitById(id: string) { return visits.find(v => v.id === id); }
export function getAssetsByBuilding(buildingId: string) { return assets.filter(a => a.buildingId === buildingId); }
export function getVisitsByTechnician(techId: string) { return visits.filter(v => v.technicianId === techId); }
export function getVisitsByDate(date: string) { return visits.filter(v => v.scheduledDate === date); }
export function getIssuesByBuilding(buildingId: string) { return issues.filter(i => i.buildingId === buildingId); }
export function getResultsByVisit(visitId: string) { return assetResults.filter(r => r.visitId === visitId); }
export function getReportsByBuilding(buildingId: string) { return reports.filter(r => r.buildingId === buildingId); }
