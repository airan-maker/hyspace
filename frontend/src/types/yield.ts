/**
 * Yield Management Types
 * 수율 관리 관련 TypeScript 타입 정의
 */

// Enums
export type YieldEventStatus =
  | 'OPEN'
  | 'INVESTIGATING'
  | 'ROOT_CAUSE_IDENTIFIED'
  | 'RESOLVED'
  | 'CLOSED';

export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type RootCauseType =
  | 'EQUIPMENT'
  | 'MATERIAL'
  | 'PROCESS'
  | 'HUMAN'
  | 'ENVIRONMENT'
  | 'UNKNOWN';

// Root Cause
export interface RootCause {
  cause_type: RootCauseType;
  entity_id: string;
  description: string;
  probability: number;
  evidence: string[];
}

// Wafer Record
export interface WaferRecord {
  id: number;
  wafer_id: string;
  lot_id: string;
  product_id?: string;
  process_step?: number;
  equipment_id?: string;
  recipe_id?: string;
  yield_percent?: number;
  die_count?: number;
  good_die_count?: number;
  defect_count?: number;
  sensor_data?: Record<string, unknown>;
  metrology_data?: Record<string, unknown>;
  defect_map?: unknown[];
  process_start?: string;
  process_end?: string;
  created_at: string;
}

// Yield Event
export interface YieldEvent {
  id: number;
  event_id: string;
  title: string;
  description?: string;
  status: YieldEventStatus;
  severity: Severity;
  yield_drop_percent: number;
  affected_wafer_count?: number;
  affected_lot_ids?: string[];
  root_causes?: RootCause[];
  analysis_summary?: string;
  recommendations?: string[];
  detected_at: string;
  resolved_at?: string;
  assigned_to?: string;
  created_by?: string;
}

export interface YieldEventCreate {
  title: string;
  description?: string;
  severity: Severity;
  yield_drop_percent: number;
  affected_wafer_ids?: string[];
  affected_lot_ids?: string[];
  process_step?: number;
  equipment_ids?: string[];
  product_ids?: string[];
  date_range_start?: string;
  date_range_end?: string;
}

export interface YieldEventUpdate {
  title?: string;
  description?: string;
  status?: YieldEventStatus;
  severity?: Severity;
  assigned_to?: string;
  analysis_summary?: string;
  recommendations?: string[];
}

// RCA (Root Cause Analysis)
export interface RCARequest {
  event_id: string;
  analysis_depth: number;
  include_similar_events: boolean;
  time_window_hours: number;
}

export interface RCAResponse {
  event_id: string;
  root_causes: RootCause[];
  confidence_score: number;
  similar_events?: string[];
  analysis_method: string;
  recommendations: string[];
  analysis_time_seconds: number;
}

// Dashboard Data
export interface YieldTrendPoint {
  date: string;
  yield_percent: number;
  wafer_count: number;
}

export interface YieldByEquipment {
  equipment_id: string;
  equipment_type: string;
  avg_yield: number;
  wafer_count: number;
  trend: 'UP' | 'DOWN' | 'STABLE';
}

export interface YieldByProduct {
  product_id: string;
  avg_yield: number;
  wafer_count: number;
}

export interface DefectType {
  type: string;
  count: number;
  percent: number;
}

export interface RecentAlert {
  time: string;
  message: string;
  severity: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface YieldDashboard {
  overall_yield: number;
  yield_target: number;
  yield_vs_target: number;
  trend_data: YieldTrendPoint[];
  by_equipment: YieldByEquipment[];
  by_product: YieldByProduct[];
  active_events: number;
  critical_events: number;
  events_this_week: number;
  top_defect_types: DefectType[];
  recent_alerts: RecentAlert[];
}

// Equipment
export interface Equipment {
  id: number;
  equipment_id: string;
  equipment_type: string;
  bay?: string;
  capacity_wph?: number;
  oee?: number;
  mtbf_hours?: number;
  mttr_hours?: number;
  status?: string;
  last_maintenance?: string;
  next_maintenance?: string;
}

// Statistics
export interface YieldStatistics {
  period_days: number;
  overall_yield: number;
  yield_target: number;
  yield_vs_target: number;
  active_events: number;
  critical_events: number;
  events_this_week: number;
  top_defect_types: DefectType[];
  equipment_count: number;
  product_count: number;
}
