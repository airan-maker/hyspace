/**
 * useWorkloadAnalysis Hook
 * 워크로드 분석 상태 관리
 */

import { useState, useCallback, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  analyzeWorkload,
  getWorkloadPresets,
  getWorkloadPreset,
  analyzePresetWorkload,
} from '../services/api';
import type {
  WorkloadProfile,
  WorkloadAnalysisResult,
  WorkloadPresetSummary,
  ComputeRequirements,
  MemoryRequirements,
  PowerConstraints,
  DeploymentContext,
} from '../types/workload';

// Default workload profile
export const defaultWorkloadProfile: WorkloadProfile = {
  name: '',
  workload_type: 'AI_INFERENCE',
  compute_requirements: {
    operations_per_inference: 100,
    target_latency_ms: 100,
    batch_size: 1,
    precision: 'INT8',
  },
  memory_requirements: {
    model_size_gb: 10,
    activation_memory_gb: 2,
    kv_cache_gb: 0,
    bandwidth_requirement_gbps: 200,
  },
  power_constraints: {
    max_tdp_watts: 200,
    target_efficiency_tops_per_watt: 2.0,
  },
  deployment_context: {
    form_factor: 'DATA_CENTER',
    cooling: 'AIR',
    volume_per_year: 10000,
  },
};

export function useWorkloadAnalysis() {
  const [profile, setProfile] = useState<WorkloadProfile>(defaultWorkloadProfile);
  const [result, setResult] = useState<WorkloadAnalysisResult | null>(null);
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);

  // Fetch presets
  const presetsQuery = useQuery({
    queryKey: ['workloadPresets'],
    queryFn: getWorkloadPresets,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Analysis mutation
  const analysisMutation = useMutation({
    mutationFn: analyzeWorkload,
    onSuccess: (data) => {
      setResult(data);
    },
  });

  // Preset analysis mutation
  const presetAnalysisMutation = useMutation({
    mutationFn: analyzePresetWorkload,
    onSuccess: (data) => {
      setResult(data);
    },
  });

  // Preset detail query (lazy)
  const loadPreset = useCallback(async (presetId: string) => {
    try {
      const presetDetail = await getWorkloadPreset(presetId);
      setProfile(presetDetail.profile);
      setSelectedPresetId(presetId);
      // Also run analysis for the preset
      presetAnalysisMutation.mutate(presetId);
    } catch (error) {
      console.error('Failed to load preset:', error);
    }
  }, []);

  // Update profile helpers
  const updateProfile = useCallback((updates: Partial<WorkloadProfile>) => {
    setProfile((prev) => ({ ...prev, ...updates }));
    setSelectedPresetId(null); // Clear preset selection when manually editing
  }, []);

  const updateComputeRequirements = useCallback(
    (updates: Partial<ComputeRequirements>) => {
      setProfile((prev) => ({
        ...prev,
        compute_requirements: { ...prev.compute_requirements, ...updates },
      }));
      setSelectedPresetId(null);
    },
    []
  );

  const updateMemoryRequirements = useCallback(
    (updates: Partial<MemoryRequirements>) => {
      setProfile((prev) => ({
        ...prev,
        memory_requirements: { ...prev.memory_requirements, ...updates },
      }));
      setSelectedPresetId(null);
    },
    []
  );

  const updatePowerConstraints = useCallback(
    (updates: Partial<PowerConstraints>) => {
      setProfile((prev) => ({
        ...prev,
        power_constraints: { ...prev.power_constraints, ...updates },
      }));
      setSelectedPresetId(null);
    },
    []
  );

  const updateDeploymentContext = useCallback(
    (updates: Partial<DeploymentContext>) => {
      setProfile((prev) => ({
        ...prev,
        deployment_context: { ...prev.deployment_context, ...updates },
      }));
      setSelectedPresetId(null);
    },
    []
  );

  // Run analysis
  const runAnalysis = useCallback(() => {
    if (!profile.name) {
      // Auto-generate name if empty
      const nameWithType = `${profile.workload_type} Workload`;
      setProfile((prev) => ({ ...prev, name: nameWithType }));
      analysisMutation.mutate({ ...profile, name: nameWithType });
    } else {
      analysisMutation.mutate(profile);
    }
  }, [profile]);

  // Reset to default
  const resetProfile = useCallback(() => {
    setProfile(defaultWorkloadProfile);
    setResult(null);
    setSelectedPresetId(null);
  }, []);

  return {
    // State
    profile,
    result,
    presets: presetsQuery.data || [],
    selectedPresetId,

    // Setters
    setProfile,
    updateProfile,
    updateComputeRequirements,
    updateMemoryRequirements,
    updatePowerConstraints,
    updateDeploymentContext,

    // Actions
    runAnalysis,
    loadPreset,
    resetProfile,

    // Loading states
    isLoading: analysisMutation.isPending || presetAnalysisMutation.isPending,
    isPresetsLoading: presetsQuery.isLoading,

    // Errors
    error: analysisMutation.error || presetAnalysisMutation.error,
    presetsError: presetsQuery.error,
  };
}
