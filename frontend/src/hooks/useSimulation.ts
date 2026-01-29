import { useState, useCallback, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { simulatePPA, simulateCost, simulatePPAAlternatives } from '../services/api';
import type { ChipConfig, PPAResult, CostResult, PPAAlternative } from '../types';

// Default chip configuration
export const defaultConfig: ChipConfig = {
  process_node_nm: 5,
  cpu_cores: 8,
  gpu_cores: 16,
  npu_cores: 4,
  l2_cache_mb: 8,
  l3_cache_mb: 32,
  pcie_lanes: 24,
  memory_channels: 4,
  target_frequency_ghz: 3.2,
};

export function useSimulation() {
  const [config, setConfig] = useState<ChipConfig>(defaultConfig);
  const [volume, setVolume] = useState(100000);
  const [targetASP, setTargetASP] = useState(100);
  const [ppaResult, setPpaResult] = useState<PPAResult | null>(null);
  const [costResult, setCostResult] = useState<CostResult | null>(null);
  const [alternatives, setAlternatives] = useState<PPAAlternative[]>([]);

  // PPA Mutation
  const ppaMutation = useMutation({
    mutationFn: simulatePPA,
    onSuccess: (data) => {
      setPpaResult(data);
    },
  });

  // Cost Mutation
  const costMutation = useMutation({
    mutationFn: simulateCost,
    onSuccess: (data) => {
      setCostResult(data);
    },
  });

  // Alternatives Mutation
  const alternativesMutation = useMutation({
    mutationFn: simulatePPAAlternatives,
    onSuccess: (data) => {
      setAlternatives(data);
    },
  });

  // Run simulation when config changes (debounced)
  const runSimulation = useCallback(() => {
    ppaMutation.mutate(config);
    alternativesMutation.mutate(config);
  }, [config]);

  // Run cost simulation when PPA result or volume/ASP changes
  const runCostSimulation = useCallback(() => {
    if (ppaResult) {
      costMutation.mutate({
        die_size_mm2: ppaResult.die_size_mm2,
        process_node_nm: config.process_node_nm,
        volume,
        target_asp: targetASP,
      });
    }
  }, [ppaResult, config.process_node_nm, volume, targetASP]);

  // Auto-run simulation on mount
  useEffect(() => {
    runSimulation();
  }, []);

  // Auto-run cost simulation when PPA result changes
  useEffect(() => {
    runCostSimulation();
  }, [ppaResult, volume, targetASP]);

  // Update config helper
  const updateConfig = useCallback((updates: Partial<ChipConfig>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  }, []);

  return {
    // State
    config,
    volume,
    targetASP,
    ppaResult,
    costResult,
    alternatives,

    // Setters
    setConfig,
    updateConfig,
    setVolume,
    setTargetASP,

    // Actions
    runSimulation,
    runCostSimulation,

    // Loading states
    isLoading: ppaMutation.isPending || costMutation.isPending,
    isPPALoading: ppaMutation.isPending,
    isCostLoading: costMutation.isPending,

    // Errors
    error: ppaMutation.error || costMutation.error,
  };
}
