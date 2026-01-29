/**
 * Yield API Service
 * 수율 관리 API 클라이언트
 */

import api from './api';
import type {
  YieldDashboard,
  YieldEvent,
  YieldEventCreate,
  YieldEventUpdate,
  RCAResponse,
  YieldTrendPoint,
  YieldByEquipment,
  YieldByProduct,
  YieldStatistics,
  Equipment,
  WaferRecord,
} from '../types/yield';

// Dashboard
export async function getYieldDashboard(
  days: number = 30,
  productId?: string
): Promise<YieldDashboard> {
  const params: Record<string, unknown> = { days };
  if (productId) params.product_id = productId;

  const { data } = await api.get<YieldDashboard>('/yield/dashboard', { params });
  return data;
}

// Trends
export async function getYieldTrends(
  days: number = 30,
  productId?: string,
  equipmentId?: string
): Promise<YieldTrendPoint[]> {
  const params: Record<string, unknown> = { days };
  if (productId) params.product_id = productId;
  if (equipmentId) params.equipment_id = equipmentId;

  const { data } = await api.get<YieldTrendPoint[]>('/yield/trends', { params });
  return data;
}

// By Equipment
export async function getYieldByEquipment(
  days: number = 30
): Promise<YieldByEquipment[]> {
  const { data } = await api.get<YieldByEquipment[]>('/yield/by-equipment', {
    params: { days },
  });
  return data;
}

// By Product
export async function getYieldByProduct(
  days: number = 30
): Promise<YieldByProduct[]> {
  const { data } = await api.get<YieldByProduct[]>('/yield/by-product', {
    params: { days },
  });
  return data;
}

// Statistics
export async function getYieldStatistics(
  days: number = 30
): Promise<YieldStatistics> {
  const { data } = await api.get<YieldStatistics>('/yield/statistics', {
    params: { days },
  });
  return data;
}

// Yield Events
export async function getYieldEvents(
  status?: string,
  severity?: string,
  startDate?: string,
  endDate?: string,
  limit: number = 50
): Promise<YieldEvent[]> {
  const params: Record<string, unknown> = { limit };
  if (status) params.status = status;
  if (severity) params.severity = severity;
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  const { data } = await api.get<YieldEvent[]>('/yield/events', { params });
  return data;
}

export async function getYieldEvent(eventId: string): Promise<YieldEvent> {
  const { data } = await api.get<YieldEvent>(`/yield/events/${eventId}`);
  return data;
}

export async function createYieldEvent(
  event: YieldEventCreate
): Promise<YieldEvent> {
  const { data } = await api.post<YieldEvent>('/yield/events', event);
  return data;
}

export async function updateYieldEvent(
  eventId: string,
  update: YieldEventUpdate
): Promise<YieldEvent> {
  const { data } = await api.put<YieldEvent>(`/yield/events/${eventId}`, update);
  return data;
}

// Root Cause Analysis
export async function analyzeRootCause(
  eventId: string,
  analysisDepth: number = 3,
  includeSimilar: boolean = true,
  timeWindowHours: number = 48
): Promise<RCAResponse> {
  const { data } = await api.post<RCAResponse>(
    `/yield/analyze/${eventId}`,
    null,
    {
      params: {
        analysis_depth: analysisDepth,
        include_similar: includeSimilar,
        time_window_hours: timeWindowHours,
      },
    }
  );
  return data;
}

// Equipment
export async function getEquipmentList(
  equipmentType?: string,
  bay?: string,
  status?: string,
  limit: number = 100
): Promise<Equipment[]> {
  const params: Record<string, unknown> = { limit };
  if (equipmentType) params.equipment_type = equipmentType;
  if (bay) params.bay = bay;
  if (status) params.status = status;

  const { data } = await api.get<Equipment[]>('/yield/equipment', { params });
  return data;
}

export async function getEquipment(equipmentId: string): Promise<Equipment> {
  const { data } = await api.get<Equipment>(`/yield/equipment/${equipmentId}`);
  return data;
}

// Wafer Records
export async function getWaferRecords(
  lotId?: string,
  equipmentId?: string,
  productId?: string,
  limit: number = 100
): Promise<WaferRecord[]> {
  const params: Record<string, unknown> = { limit };
  if (lotId) params.lot_id = lotId;
  if (equipmentId) params.equipment_id = equipmentId;
  if (productId) params.product_id = productId;

  const { data } = await api.get<WaferRecord[]>('/yield/wafers', { params });
  return data;
}

export async function getWaferRecord(waferId: string): Promise<WaferRecord> {
  const { data } = await api.get<WaferRecord>(`/yield/wafers/${waferId}`);
  return data;
}
