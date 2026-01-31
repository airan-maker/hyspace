import { useState, useCallback } from 'react';
import {
  getGraphStatus,
  migrateGraph,
  getGraphVisualization,
  getAcceleratorContext,
  getAcceleratorSupplyRisks,
  getProcessFlowWithRisks,
  getEquipmentImpact,
  getMaterialDependency,
  getCriticalSupplyRisks,
  findGraphPath,
  runCypherQuery,
  type GraphStatus,
  type GraphVisualizationData,
} from '../services/api';

export interface PresetQuery {
  id: string;
  label: string;
  description: string;
  execute: () => Promise<unknown>;
}

export function useGraphExplorer() {
  const [status, setStatus] = useState<GraphStatus | null>(null);
  const [vizData, setVizData] = useState<GraphVisualizationData | null>(null);
  const [queryResult, setQueryResult] = useState<unknown>(null);
  const [selectedQuery, setSelectedQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isMigrating, setIsMigrating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getGraphStatus();
      setStatus(data);
    } catch {
      setStatus({ available: false, message: 'Failed to connect to Neo4j' });
    }
  }, []);

  const runMigration = useCallback(async () => {
    setIsMigrating(true);
    setError(null);
    try {
      const result = await migrateGraph();
      await fetchStatus();
      return result;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Migration failed';
      setError(msg);
      throw e;
    } finally {
      setIsMigrating(false);
    }
  }, [fetchStatus]);

  const fetchVisualization = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getGraphVisualization();
      setVizData(data);
    } catch {
      setError('Failed to load graph visualization');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const executePreset = useCallback(async (presetId: string) => {
    setIsLoading(true);
    setError(null);
    setSelectedQuery(presetId);
    setQueryResult(null);
    try {
      let result: unknown;
      switch (presetId) {
        case 'h100_context':
          result = await getAcceleratorContext('H100');
          break;
        case 'h100_supply_risks':
          result = await getAcceleratorSupplyRisks('H100');
          break;
        case 'b200_supply_risks':
          result = await getAcceleratorSupplyRisks('B200');
          break;
        case 'process_flow':
          result = await getProcessFlowWithRisks();
          break;
        case 'euv_impact':
          result = await getEquipmentImpact('ASML');
          break;
        case 'euv_resist_dep':
          result = await getMaterialDependency('EUV');
          break;
        case 'critical_materials':
          result = await getCriticalSupplyRisks();
          break;
        case 'h100_to_euv':
          result = await findGraphPath('H100', 'EUV Photoresist');
          break;
        default:
          break;
      }
      setQueryResult(result);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Query failed';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const executeCypher = useCallback(async (cypher: string) => {
    setIsLoading(true);
    setError(null);
    setSelectedQuery('custom');
    setQueryResult(null);
    try {
      const result = await runCypherQuery(cypher);
      setQueryResult(result);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Query failed';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const presets: PresetQuery[] = [
    { id: 'h100_context', label: 'H100 전체 컨텍스트', description: '공정, 메모리, 패키징, 호환 모델 (1-hop)', execute: () => executePreset('h100_context') },
    { id: 'h100_supply_risks', label: 'H100 공급망 리스크', description: '가속기→공정→소재 경로의 HIGH 리스크 (multi-hop)', execute: () => executePreset('h100_supply_risks') },
    { id: 'b200_supply_risks', label: 'B200 공급망 리스크', description: 'Blackwell 공급망 리스크 분석', execute: () => executePreset('b200_supply_risks') },
    { id: 'process_flow', label: '전체 공정 플로우', description: '13단계 + 결함/장비/소재 리스크', execute: () => executePreset('process_flow') },
    { id: 'euv_impact', label: 'EUV 장비 고장 영향', description: 'ASML 장비 고장 시 전체 영향 분석', execute: () => executePreset('euv_impact') },
    { id: 'euv_resist_dep', label: 'EUV 레지스트 의존성', description: '소재 공급 중단 시 영향 체인', execute: () => executePreset('euv_resist_dep') },
    { id: 'critical_materials', label: '핵심 소재 리스크', description: 'HIGH 이상 공급 리스크 소재 목록', execute: () => executePreset('critical_materials') },
    { id: 'h100_to_euv', label: 'H100↔EUV 경로', description: '가속기~소재 간 관계 경로 탐색', execute: () => executePreset('h100_to_euv') },
  ];

  return {
    status,
    vizData,
    queryResult,
    selectedQuery,
    isLoading,
    isMigrating,
    error,
    presets,
    fetchStatus,
    runMigration,
    fetchVisualization,
    executePreset,
    executeCypher,
  };
}
