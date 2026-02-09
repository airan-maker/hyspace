import { useState, useCallback, useEffect } from 'react';
import {
  getWhatIfPresets,
  executeWhatIf,
  type WhatIfPreset,
  type WhatIfResponse,
} from '../services/api';

export function useWhatIf() {
  const [presets, setPresets] = useState<WhatIfPreset[]>([]);
  const [result, setResult] = useState<WhatIfResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getWhatIfPresets()
      .then(d => setPresets(d.presets))
      .catch(() => {});
  }, []);

  const execute = useCallback(async (
    scenarioType: string,
    targetEntity: string,
    delayMonths: number,
    includeNarrative: boolean = false,
  ) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await executeWhatIf(scenarioType, targetEntity, delayMonths, includeNarrative);
      setResult(data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '시나리오 실행 실패';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const executePreset = useCallback(async (preset: WhatIfPreset, includeNarrative: boolean = false) => {
    await execute(preset.scenario_type, preset.target_entity, preset.delay_months, includeNarrative);
  }, [execute]);

  const clear = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    presets,
    result,
    isLoading,
    error,
    execute,
    executePreset,
    clear,
  };
}
