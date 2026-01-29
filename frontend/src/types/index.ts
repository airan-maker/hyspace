// Chip Configuration
export interface ChipConfig {
  process_node_nm: number;
  cpu_cores: number;
  gpu_cores: number;
  npu_cores: number;
  l2_cache_mb: number;
  l3_cache_mb: number;
  pcie_lanes: number;
  memory_channels: number;
  target_frequency_ghz: number;
}

// Area Breakdown
export interface AreaBreakdown {
  cpu: number;
  gpu: number;
  npu: number;
  l2_cache: number;
  l3_cache: number;
  io: number;
  memory_controller: number;
  overhead: number;
  total: number;
}

// Power Breakdown
export interface PowerBreakdown {
  cpu: number;
  gpu: number;
  npu: number;
  cache: number;
  io: number;
  total: number;
}

// PPA Result
export interface PPAResult {
  die_size_mm2: number;
  power_tdp_w: number;
  performance_ghz: number;
  performance_tops: number;
  efficiency_tops_per_watt: number;
  confidence_score: number;
  area_breakdown: AreaBreakdown;
  power_breakdown: PowerBreakdown;
}

// Cost Result
export interface CostResult {
  wafer_cost: number;
  die_cost: number;
  good_die_cost: number;
  package_cost: number;
  test_cost: number;
  total_unit_cost: number;
  target_asp: number;
  gross_margin: number;
  gross_margin_percent: number;
  net_die_per_wafer: number;
  yield_rate: number;
}

// Full Simulation Result
export interface SimulationResult {
  id: string;
  name?: string;
  config: ChipConfig;
  ppa: PPAResult;
  cost: CostResult;
  confidence_score: number;
  created_at: string;
}

// Process Node
export interface ProcessNode {
  id: number;
  name: string;
  node_nm: number;
  wafer_cost: number;
  defect_density: number;
  base_core_area: number;
  cache_density: number;
  io_area_per_lane: number;
  power_density: number;
  max_frequency_ghz: number;
  is_active: boolean;
}

// IP Block
export interface IPBlock {
  id: number;
  name: string;
  type: string;
  vendor?: string;
  version?: string;
  area_mm2: number;
  power_mw: number;
  performance_metric?: number;
  performance_unit?: string;
  silicon_proven: boolean;
  compatible_nodes?: number[];
  description?: string;
}

// Alternative Configuration
export interface PPAAlternative {
  variant: string;
  result: PPAResult;
}

// Volume Economics
export interface VolumeEconomics {
  volume: number;
  unit_cost: number;
  total_cost: number;
  volume_discount: number;
  break_even_volume: number;
}
