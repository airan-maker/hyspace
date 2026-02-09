import axios from 'axios';
import type {
  ChipConfig,
  PPAResult,
  CostResult,
  SimulationResult,
  ProcessNode,
  IPBlock,
  PPAAlternative,
  VolumeEconomics,
} from '../types';
import type {
  WorkloadProfile,
  WorkloadAnalysisResult,
  WorkloadPresetSummary,
  WorkloadPresetDetail,
} from '../types/workload';

// 환경변수에서 API URL 가져오기 (프로덕션 배포 시 설정)
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// PPA Simulation
export async function simulatePPA(config: ChipConfig): Promise<PPAResult> {
  const { data } = await api.post<PPAResult>('/simulate/ppa', config);
  return data;
}

// PPA Alternatives
export async function simulatePPAAlternatives(config: ChipConfig): Promise<PPAAlternative[]> {
  const { data } = await api.post<{ alternatives: PPAAlternative[] }>('/simulate/ppa/alternatives', config);
  return data.alternatives;
}

// Cost Simulation
export interface CostRequest {
  die_size_mm2: number;
  process_node_nm: number;
  volume: number;
  target_asp: number;
}

export async function simulateCost(request: CostRequest): Promise<CostResult> {
  const { data } = await api.post<CostResult>('/simulate/cost', request);
  return data;
}

// Volume Analysis
export interface VolumeAnalysisRequest {
  die_size_mm2: number;
  process_node_nm: number;
  target_asp: number;
  volumes?: number[];
}

export async function analyzeVolume(request: VolumeAnalysisRequest): Promise<VolumeEconomics[]> {
  const { data } = await api.post<{ analysis: VolumeEconomics[] }>('/simulate/cost/volume-analysis', request);
  return data.analysis;
}

// Full Simulation
export interface FullSimulationRequest {
  name?: string;
  config: ChipConfig;
  volume: number;
  target_asp: number;
}

export async function runFullSimulation(request: FullSimulationRequest): Promise<SimulationResult> {
  const { data } = await api.post<SimulationResult>('/simulate/full', request);
  return data;
}

// Get Simulation History
export async function getSimulationHistory(skip = 0, limit = 20): Promise<SimulationResult[]> {
  const { data } = await api.get<SimulationResult[]>('/simulate/history', {
    params: { skip, limit },
  });
  return data;
}

// Get Simulation by ID
export async function getSimulation(id: string): Promise<SimulationResult> {
  const { data } = await api.get<SimulationResult>(`/simulate/${id}`);
  return data;
}

// Reference Data
export async function getProcessNodes(): Promise<ProcessNode[]> {
  const { data } = await api.get<ProcessNode[]>('/reference/process-nodes');
  return data;
}

export async function getIPLibrary(type?: string): Promise<IPBlock[]> {
  const { data } = await api.get<IPBlock[]>('/reference/ip-library', {
    params: type ? { ip_type: type } : {},
  });
  return data;
}

// Workload Analysis
export async function analyzeWorkload(profile: WorkloadProfile): Promise<WorkloadAnalysisResult> {
  const { data } = await api.post<WorkloadAnalysisResult>('/workload/analyze', profile);
  return data;
}

export async function getWorkloadPresets(): Promise<WorkloadPresetSummary[]> {
  const { data } = await api.get<{ presets: WorkloadPresetSummary[] }>('/workload/presets');
  return data.presets;
}

export async function getWorkloadPreset(id: string): Promise<WorkloadPresetDetail> {
  const { data } = await api.get<WorkloadPresetDetail>(`/workload/presets/${id}`);
  return data;
}

export async function analyzePresetWorkload(presetId: string): Promise<WorkloadAnalysisResult> {
  const { data } = await api.post<WorkloadAnalysisResult>(`/workload/presets/${presetId}/analyze`);
  return data;
}

// Seed Data Agent
export interface SeedScenario {
  scenario_id: string;
  name: string;
  name_kr: string;
  description: string;
  process_node: string;
  target_product: string;
  tags: string[];
  wspm?: number;
  equipment_count?: number;
  wip_lots?: number;
  history_days?: number;
}

export interface SeedPreview {
  scenario: { id: string; name: string; process_node: string };
  summary: {
    scenario: string;
    process_node: string;
    generated_at: string;
    data_counts: Record<string, string>;
    ontology_sources: string[];
  };
  [key: string]: unknown;
}

export interface SeedApplyResult {
  status: string;
  scenario: { id: string; name: string };
  loaded: Record<string, { created: number; skipped: number }>;
  message: string;
}

export interface SeedStatus {
  process_nodes: number;
  ip_blocks: number;
  fab_equipment: number;
  wip_items: number;
  materials: number;
  suppliers: number;
  wafer_records: number;
  yield_events: number;
}

export async function getSeedScenarios(): Promise<{ count: number; scenarios: SeedScenario[] }> {
  const { data } = await api.get('/seed/scenarios');
  return data;
}

export async function getSeedScenarioDetail(id: string): Promise<SeedScenario> {
  const { data } = await api.get(`/seed/scenarios/${id}`);
  return data;
}

export async function previewSeedData(scenarioId: string): Promise<SeedPreview> {
  const { data } = await api.post(`/seed/preview/${scenarioId}`);
  return data;
}

export async function applySeedData(scenarioId: string, clearExisting: boolean = false): Promise<SeedApplyResult> {
  const { data } = await api.post(`/seed/apply/${scenarioId}?clear_existing=${clearExisting}`);
  return data;
}

export async function getSeedStatus(): Promise<SeedStatus> {
  const { data } = await api.get('/seed/status');
  return data;
}

export async function clearSeedData(): Promise<{ status: string; deleted: Record<string, number> }> {
  const { data } = await api.delete('/seed/clear?confirm=true');
  return data;
}

// ─────────────────────────────────────────────────────
// Graph API
// ─────────────────────────────────────────────────────

export interface GraphStatus {
  available: boolean;
  nodes?: Record<string, number>;
  relationships?: Record<string, number>;
  total_nodes?: number;
  total_relationships?: number;
  message?: string;
}

export interface GraphNode {
  id: number;
  label: string;
  name: string;
  properties: Record<string, unknown>;
}

export interface GraphLink {
  source: number;
  target: number;
  type: string;
}

export interface GraphVisualizationData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export async function getGraphStatus(): Promise<GraphStatus> {
  const { data } = await api.get('/graph/status');
  return data;
}

export async function migrateGraph(): Promise<{ status: string; stats: Record<string, unknown> }> {
  const { data } = await api.post('/graph/migrate');
  return data;
}

export async function getAcceleratorContext(name: string): Promise<Record<string, unknown>> {
  const { data } = await api.get(`/graph/accelerator/${encodeURIComponent(name)}/context`);
  return data;
}

export async function getAcceleratorSupplyRisks(name: string): Promise<{ accelerator: string; risks: Record<string, unknown>[]; count: number }> {
  const { data } = await api.get(`/graph/accelerator/${encodeURIComponent(name)}/supply-risks`);
  return data;
}

export async function getProcessFlowWithRisks(): Promise<{ steps: Record<string, unknown>[] }> {
  const { data } = await api.get('/graph/process-flow');
  return data;
}

export async function getEquipmentImpact(name: string): Promise<Record<string, unknown>> {
  const { data } = await api.get(`/graph/equipment/${encodeURIComponent(name)}/impact`);
  return data;
}

export async function getMaterialDependency(name: string): Promise<Record<string, unknown>> {
  const { data } = await api.get(`/graph/material/${encodeURIComponent(name)}/dependency`);
  return data;
}

export async function getCriticalSupplyRisks(): Promise<{ materials: Record<string, unknown>[]; count: number }> {
  const { data } = await api.get('/graph/materials/critical-risks');
  return data;
}

export async function findGraphPath(from: string, to: string): Promise<{ paths: Record<string, unknown>[]; count: number }> {
  const { data } = await api.get('/graph/path', { params: { from, to } });
  return data;
}

export async function getGraphVisualization(): Promise<GraphVisualizationData> {
  const { data } = await api.get('/graph/visualization');
  return data;
}

export async function runCypherQuery(cypher: string, params?: Record<string, unknown>): Promise<{ results: Record<string, unknown>[]; count: number }> {
  const { data } = await api.post('/graph/query', { cypher, params });
  return data;
}

// ─────────────────────────────────────────────────────
// AI Insights API
// ─────────────────────────────────────────────────────

export interface InsightRequest {
  query_type: string;
  results: unknown;
}

export async function generateInsight(queryType: string, results: unknown): Promise<{ insight: string; query_type: string }> {
  const { data } = await api.post('/graph/insight', { query_type: queryType, results });
  return data;
}

export function generateInsightStreamURL(): string {
  return `${API_BASE_URL}/api/graph/insight/stream`;
}

// ─────────────────────────────────────────────────────
// What-If Simulation API
// ─────────────────────────────────────────────────────

export interface WhatIfPreset {
  id: string;
  label: string;
  description: string;
  scenario_type: string;
  target_entity: string;
  delay_months: number;
}

export interface AffectedNode {
  id: number;
  label: string;
  name: string;
  severity: string;
  impact_reason: string;
}

export interface WhatIfResponse {
  scenario: Record<string, unknown>;
  affected_nodes: AffectedNode[];
  affected_node_ids: number[];
  total_affected: number;
  alternatives: Record<string, unknown>[];
  narrative: string | null;
}

export async function getWhatIfPresets(): Promise<{ presets: WhatIfPreset[] }> {
  const { data } = await api.get('/graph/whatif/presets');
  return data;
}

export async function executeWhatIf(
  scenarioType: string,
  targetEntity: string,
  delayMonths: number,
  includeNarrative: boolean = true,
): Promise<WhatIfResponse> {
  const { data } = await api.post('/graph/whatif', {
    scenario_type: scenarioType,
    target_entity: targetEntity,
    delay_months: delayMonths,
    include_ai_narrative: includeNarrative,
  });
  return data;
}

// ── Graph Search ──

export interface SearchResultNode {
  id: string;
  name: string;
  label: string;
  labels: string[];
  connection_count: number;
  properties: Record<string, unknown>;
}

export async function searchGraphNodes(params: {
  q?: string;
  label?: string;
  risk?: string;
  limit?: number;
}): Promise<{ results: SearchResultNode[]; count: number }> {
  const { data } = await api.get('/graph/search', { params });
  return data;
}

export async function getGraphLabels(): Promise<{ labels: string[] }> {
  const { data } = await api.get('/graph/labels');
  return data;
}

export interface TemplateOptions {
  accelerators: string[];
  equipment_vendors: string[];
  materials: string[];
  all_nodes: string[];
}

export async function getTemplateOptions(): Promise<TemplateOptions> {
  const { data } = await api.get<TemplateOptions>('/graph/template-options');
  return data;
}

// ── Geospatial ──

export interface SupplierLocation {
  vendor: string;
  lat: number;
  lng: number;
  country: string;
  city: string;
  node_label: string;
  node_name: string;
  risk: string | null;
  criticality: string | null;
}

export async function getSupplierLocations(): Promise<{ suppliers: SupplierLocation[]; count: number }> {
  const { data } = await api.get('/graph/geospatial/suppliers');
  return data;
}

// ── Yield-Graph Bridge ──

export interface GraphContextNode {
  id: string;
  label: string;
  name: string;
  properties: Record<string, unknown>;
}

export interface GraphContextResult {
  nodes: GraphContextNode[];
  relationships: { type: string; from: string; to: string }[];
  suggested_queries: string[];
}

export async function getGraphContextForEvent(params: {
  process_step?: string;
  equipment_id?: string;
  material?: string;
}): Promise<GraphContextResult> {
  const { data } = await api.post('/graph/context-from-event', params);
  return data;
}

export default api;
