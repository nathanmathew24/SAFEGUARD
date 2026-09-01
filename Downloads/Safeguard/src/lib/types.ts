export type TradeType = 'fire' | 'hvac' | 'elv';
export type StatusType = 'ok' | 'warning' | 'critical';
export type VisitStatus = 'scheduled' | 'in-progress' | 'completed' | 'overdue';
export type AssetStatus = 'pass' | 'fail' | 'pending' | 'expired';
export type IssuePriority = 'high' | 'medium' | 'low';
export type IssueStatus = 'open' | 'in-progress' | 'resolved';
export type Emirate = 'Dubai' | 'Sharjah' | 'Abu Dhabi' | 'Ajman' | 'RAK';

export interface Trade {
  id: TradeType;
  label: string;
  description: string;
}

export interface Building {
  id: string;
  name: string;
  address: string;
  emirate: Emirate;
  health: StatusType;
  tradeHealth: Record<TradeType, StatusType | null>;
  trades: TradeType[];
  assignedTechnicianIds: string[];
  ownerContact: { name: string; phone: string; email: string };
  assetCount: number;
  nextInspection: string;
  lastInspection: string;
}

export interface Asset {
  id: string;
  tag: string;
  buildingId: string;
  trade: TradeType;
  type: string;
  status: AssetStatus;
  lastChecked: string;
  nextDue: string;
  photoHistory: string[];
}

export interface Technician {
  id: string;
  name: string;
  initials: string;
  trades: TradeType[];
  phone: string;
  email: string;
  activeJobCount: number;
}

export interface Visit {
  id: string;
  buildingId: string;
  technicianId: string;
  trade: TradeType;
  scheduledDate: string;
  scheduledTime: string;
  status: VisitStatus;
  assetIds: string[];
  completedAt?: string;
}

export interface AssetResult {
  id: string;
  visitId: string;
  assetId: string;
  pass: boolean;
  photo?: string;
  timestamp: string;
  technicianId: string;
  deviceMeta: string;
  synced: boolean;
}

export interface Issue {
  id: string;
  assetId: string;
  buildingId: string;
  trade: TradeType;
  type: 'failed-asset' | 'expired-cert' | 'overdue-inspection';
  priority: IssuePriority;
  status: IssueStatus;
  assignedToId?: string;
  createdAt: string;
  description: string;
}

export interface Report {
  id: string;
  buildingId: string;
  trades: TradeType[];
  dateRange: { from: string; to: string };
  generatedAt: string;
  documentUrl: string;
  title: string;
}

export interface InspectionRule {
  id: string;
  emirate: Emirate;
  trade: TradeType;
  assetType: string;
  frequencyDays: number;
  standard: string;
}
