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

export default api;
