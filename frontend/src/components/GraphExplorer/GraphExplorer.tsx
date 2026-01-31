import { useEffect, useState } from 'react';
import { useGraphExplorer } from '../../hooks/useGraphExplorer';

// Label → color mapping for graph nodes
const LABEL_COLORS: Record<string, string> = {
  AIAccelerator: '#f59e0b',
  ProcessNode: '#3b82f6',
  HBMGeneration: '#8b5cf6',
  PackagingTech: '#06b6d4',
  AIModel: '#ec4899',
  Material: '#ef4444',
  Equipment: '#10b981',
  ProcessStep: '#6366f1',
  DefectType: '#f97316',
  EquipmentFailure: '#dc2626',
};

function StatusBanner({ status, onMigrate, isMigrating }: {
  status: { available: boolean; total_nodes?: number; total_relationships?: number; message?: string } | null;
  onMigrate: () => void;
  isMigrating: boolean;
}) {
  if (!status) return null;

  if (!status.available) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2">
          <span className="text-red-600 font-medium">Neo4j 미연결</span>
          <span className="text-red-500 text-sm">{status.message || 'docker-compose up neo4j 실행 필요'}</span>
        </div>
      </div>
    );
  }

  const isEmpty = (status.total_nodes || 0) === 0;

  return (
    <div className={`${isEmpty ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'} border rounded-lg p-4 mb-6`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className={`${isEmpty ? 'text-yellow-600' : 'text-green-600'} font-medium`}>
            {isEmpty ? 'Neo4j 연결됨 (데이터 없음)' : 'Neo4j 연결됨'}
          </span>
          {!isEmpty && (
            <span className="text-sm text-gray-500">
              노드: {status.total_nodes} | 관계: {status.total_relationships}
            </span>
          )}
        </div>
        <button
          onClick={onMigrate}
          disabled={isMigrating}
          className="px-3 py-1.5 text-sm bg-nexus-600 text-white rounded-lg hover:bg-nexus-700 disabled:opacity-50"
        >
          {isMigrating ? '마이그레이션 중...' : isEmpty ? '온톨로지 마이그레이션' : '재마이그레이션'}
        </button>
      </div>
    </div>
  );
}

function QueryPanel({ presets, selectedQuery, onSelect, isLoading }: {
  presets: { id: string; label: string; description: string }[];
  selectedQuery: string;
  onSelect: (id: string) => void;
  isLoading: boolean;
}) {
  return (
    <div className="card mb-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">프리셋 그래프 질의</h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
        {presets.map((preset) => (
          <button
            key={preset.id}
            onClick={() => onSelect(preset.id)}
            disabled={isLoading}
            className={`text-left p-3 rounded-lg border transition-all ${
              selectedQuery === preset.id
                ? 'border-nexus-500 bg-nexus-50 ring-1 ring-nexus-500'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            } disabled:opacity-50`}
          >
            <div className="text-sm font-medium text-gray-800">{preset.label}</div>
            <div className="text-xs text-gray-500 mt-0.5">{preset.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

function CypherInput({ onExecute, isLoading }: {
  onExecute: (cypher: string) => void;
  isLoading: boolean;
}) {
  const [cypher, setCypher] = useState('');

  return (
    <div className="card mb-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Cypher 직접 질의</h3>
      <div className="flex gap-2">
        <input
          type="text"
          value={cypher}
          onChange={(e) => setCypher(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && cypher.trim()) onExecute(cypher); }}
          placeholder="MATCH (n:AIAccelerator) RETURN n.name, n.tdp_watts LIMIT 10"
          className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-nexus-500 focus:border-nexus-500 font-mono"
        />
        <button
          onClick={() => { if (cypher.trim()) onExecute(cypher); }}
          disabled={isLoading || !cypher.trim()}
          className="px-4 py-2 text-sm bg-gray-800 text-white rounded-lg hover:bg-gray-900 disabled:opacity-50"
        >
          실행
        </button>
      </div>
    </div>
  );
}

function GraphOverview({ status }: { status: { nodes?: Record<string, number>; relationships?: Record<string, number> } }) {
  const nodes = status.nodes || {};
  const rels = status.relationships || {};

  return (
    <div className="card mb-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">그래프 구조</h3>
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h4 className="text-xs font-medium text-gray-500 mb-2">노드 (Labels)</h4>
          <div className="space-y-1">
            {Object.entries(nodes).map(([label, count]) => (
              <div key={label} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full" style={{ backgroundColor: LABEL_COLORS[label] || '#9ca3af' }} />
                  <span className="text-gray-700">{label}</span>
                </div>
                <span className="text-gray-500 font-mono">{count}</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <h4 className="text-xs font-medium text-gray-500 mb-2">관계 (Relationships)</h4>
          <div className="space-y-1">
            {Object.entries(rels).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between text-sm">
                <span className="text-gray-700 font-mono text-xs">{type}</span>
                <span className="text-gray-500 font-mono">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ResultPanel({ result, selectedQuery, isLoading, error }: {
  result: unknown;
  selectedQuery: string;
  isLoading: boolean;
  error: string | null;
}) {
  if (isLoading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-nexus-200 border-t-nexus-600 rounded-full" />
          <span className="ml-3 text-gray-500">쿼리 실행 중...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card border-red-200 bg-red-50">
        <p className="text-red-600 text-sm">{error}</p>
      </div>
    );
  }

  if (!result || !selectedQuery) {
    return (
      <div className="card">
        <div className="text-center py-12">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-4.486a4.5 4.5 0 00-6.364-6.364L5.265 6.264a4.5 4.5 0 001.242 7.244" />
          </svg>
          <p className="text-gray-500">프리셋 질의를 선택하거나 Cypher를 직접 입력하세요</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">결과</h3>
      <div className="bg-gray-50 rounded-lg p-4 overflow-auto max-h-[600px]">
        <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap">
          {JSON.stringify(result, null, 2)}
        </pre>
      </div>
    </div>
  );
}

export default function GraphExplorer() {
  const {
    status,
    queryResult,
    selectedQuery,
    isLoading,
    isMigrating,
    error,
    presets,
    fetchStatus,
    runMigration,
    executePreset,
    executeCypher,
  } = useGraphExplorer();

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Graph Explorer</h1>
        <p className="text-gray-500 mt-1">
          Neo4j 그래프 데이터베이스를 탐색하고 도메인 관계를 질의합니다.
        </p>
      </div>

      <StatusBanner status={status} onMigrate={runMigration} isMigrating={isMigrating} />

      {status?.available && (status.total_nodes || 0) > 0 && (
        <>
          <GraphOverview status={status} />
          <QueryPanel
            presets={presets}
            selectedQuery={selectedQuery}
            onSelect={executePreset}
            isLoading={isLoading}
          />
          <CypherInput onExecute={executeCypher} isLoading={isLoading} />
          <ResultPanel
            result={queryResult}
            selectedQuery={selectedQuery}
            isLoading={isLoading}
            error={error}
          />
        </>
      )}
    </>
  );
}
