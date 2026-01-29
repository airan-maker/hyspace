/**
 * Workload Analysis Types
 * 워크로드 분석 관련 TypeScript 타입 정의
 */

// Enums
export type WorkloadType =
  | 'AI_INFERENCE'
  | 'AI_TRAINING'
  | 'IMAGE_PROCESSING'
  | 'VIDEO_ENCODING'
  | 'SCIENTIFIC_COMPUTE'
  | 'GENERAL_PURPOSE'
  | 'EDGE_INFERENCE';

export type FormFactor = 'DATA_CENTER' | 'EDGE_SERVER' | 'EMBEDDED' | 'MOBILE';

export type CoolingType = 'AIR' | 'LIQUID' | 'PASSIVE';

export type Precision = 'FP32' | 'FP16' | 'BF16' | 'INT8' | 'INT4';

export type MemoryType = 'HBM3' | 'HBM3E' | 'HBM4' | 'GDDR6' | 'LPDDR5';

// Request types
export interface ComputeRequirements {
  operations_per_inference: number;
  target_latency_ms: number;
  batch_size: number;
  precision: Precision;
}

export interface MemoryRequirements {
  model_size_gb: number;
  activation_memory_gb: number;
  kv_cache_gb: number;
  bandwidth_requirement_gbps: number;
}

export interface PowerConstraints {
  max_tdp_watts: number;
  target_efficiency_tops_per_watt: number;
}

export interface DeploymentContext {
  form_factor: FormFactor;
  cooling: CoolingType;
  volume_per_year: number;
}

export interface WorkloadProfile {
  name: string;
  workload_type: WorkloadType;
  compute_requirements: ComputeRequirements;
  memory_requirements: MemoryRequirements;
  power_constraints: PowerConstraints;
  deployment_context: DeploymentContext;
  description?: string;
}

// Response types
export interface WorkloadCharacterization {
  compute_intensity: string;
  arithmetic_intensity: number;
  bottleneck: string;
  required_tops: number;
}

export interface RecommendedArchitecture {
  name: string;
  description: string;
  process_node_nm: number;
  npu_cores: number;
  cpu_cores: number;
  gpu_cores: number;
  memory_type: MemoryType;
  memory_capacity_gb: number;
  memory_bandwidth_tbps: number;
  die_size_mm2: number;
  power_tdp_w: number;
  performance_tops: number;
  efficiency_tops_per_watt: number;
  estimated_unit_cost: number;
  match_score: number;
  is_recommended: boolean;
  justifications: string[];
  trade_offs: string[];
}

export interface CompetitiveBenchmark {
  competitor_name: string;
  performance_tops: number;
  power_tdp_w: number;
  memory_bandwidth_tbps: number;
  estimated_price: number;
  comparison_summary: string;
}

export interface WorkloadAnalysisResult {
  workload_name: string;
  workload_type: WorkloadType;
  characterization: WorkloadCharacterization;
  recommended_architectures: RecommendedArchitecture[];
  competitive_benchmarks: CompetitiveBenchmark[];
  confidence_score: number;
  analysis_notes: string[];
}

// Preset types
export interface WorkloadPresetSummary {
  id: string;
  name: string;
  category: string;
  description: string;
}

export interface WorkloadPresetDetail {
  id: string;
  name: string;
  category: string;
  description: string;
  profile: WorkloadProfile;
}

// UI State types
export interface WorkloadAnalysisState {
  profile: WorkloadProfile;
  result: WorkloadAnalysisResult | null;
  presets: WorkloadPresetSummary[];
  isLoading: boolean;
  isPresetsLoading: boolean;
  error: Error | null;
}
