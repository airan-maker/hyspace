import { useState } from 'react';
import { useWhatIf } from '../../hooks/useWhatIf';
import { LABEL_COLORS } from './constants';
import type { AffectedNode } from '../../services/api';

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#dc2626',
  HIGH: '#ea580c',
  MEDIUM: '#ca8a04',
  LOW: '#65a30d',
};

function SeverityDot({ severity }: { severity: string }) {
  return (
    <span
      className="inline-block w-2 h-2 rounded-full flex-shrink-0"
      style={{ backgroundColor: SEVERITY_COLORS[severity] || '#9ca3af' }}
    />
  );
}

interface WhatIfPanelProps {
  onAffectedNodesChange?: (nodeIds: number[]) => void;
}

export default function WhatIfPanel({ onAffectedNodesChange }: WhatIfPanelProps) {
  const { presets, result, isLoading, error, executePreset, clear } = useWhatIf();
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
  const [showNarrative, setShowNarrative] = useState(false);

  const handleExecute = async (presetId: string) => {
    const preset = presets.find(p => p.id === presetId);
    if (!preset) return;
    setSelectedPresetId(presetId);
    await executePreset(preset, showNarrative);
  };

  // 영향 노드 변경 시 부모에 알림
  if (result && onAffectedNodesChange) {
    // 콜백은 렌더 외부에서 호출해야 하지만, 간단히 처리
    setTimeout(() => onAffectedNodesChange(result.affected_node_ids), 0);
  }

  const handleClear = () => {
    clear();
    setSelectedPresetId(null);
    onAffectedNodesChange?.([]);
  };

  // 심각도별 그룹
  const grouped = result?.affected_nodes.reduce<Record<string, AffectedNode[]>>((acc, node) => {
    (acc[node.severity] ??= []).push(node);
    return acc;
  }, {}) ?? {};

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">What-If 시나리오 분석</h3>
        {result && (
          <button onClick={handleClear} className="text-xs text-gray-400 hover:text-red-500">
            초기화
          </button>
        )}
      </div>
      <p className="text-xs text-gray-500 mb-4">
        공급망 시나리오를 선택하면 영향받는 노드를 그래프에서 하이라이트합니다.
      </p>

      {/* 프리셋 버튼 */}
      <div className="flex flex-wrap gap-2 mb-4">
        {presets.map(p => (
          <button
            key={p.id}
            onClick={() => handleExecute(p.id)}
            disabled={isLoading}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
              selectedPresetId === p.id
                ? 'border-red-400 bg-red-50 text-red-700 font-medium'
                : 'border-gray-200 bg-white text-gray-600 hover:border-red-300 hover:bg-red-50/50'
            } disabled:opacity-50`}
            title={p.description}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* AI 내러티브 토글 */}
      <label className="flex items-center gap-2 text-xs text-gray-500 mb-3">
        <input
          type="checkbox"
          checked={showNarrative}
          onChange={e => setShowNarrative(e.target.checked)}
          className="rounded border-gray-300"
        />
        AI 영향 분석 내러티브 포함 (응답 시간 증가)
      </label>

      {/* 로딩 */}
      {isLoading && (
        <div className="flex items-center gap-2 py-6 justify-center">
          <div className="animate-spin w-5 h-5 border-2 border-red-200 border-t-red-600 rounded-full" />
          <span className="text-sm text-gray-500">시나리오 분석 중...</span>
        </div>
      )}

      {/* 에러 */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* 결과 */}
      {result && !isLoading && (
        <div className="space-y-4">
          {/* 요약 */}
          <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{result.total_affected}</div>
              <div className="text-xs text-gray-500">영향 노드</div>
            </div>
            {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(sev => {
              const count = grouped[sev]?.length ?? 0;
              if (count === 0) return null;
              return (
                <div key={sev} className="text-center">
                  <div className="flex items-center gap-1">
                    <SeverityDot severity={sev} />
                    <span className="text-lg font-semibold" style={{ color: SEVERITY_COLORS[sev] }}>
                      {count}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">{sev}</div>
                </div>
              );
            })}
          </div>

          {/* 영향 노드 목록 */}
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {result.affected_nodes.map(node => (
              <div
                key={node.id}
                className="flex items-start gap-2 p-2 rounded-md hover:bg-gray-50 text-sm"
              >
                <SeverityDot severity={node.severity} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: LABEL_COLORS[node.label] || '#9ca3af' }}
                    />
                    <span className="font-medium text-gray-800 truncate">{node.name}</span>
                    <span className="text-xs text-gray-400">{node.label}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{node.impact_reason}</p>
                </div>
              </div>
            ))}
          </div>

          {/* AI 내러티브 */}
          {result.narrative && (
            <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
              <h4 className="text-xs font-semibold text-purple-700 mb-2">AI 영향 분석</h4>
              <div className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
                {result.narrative}
              </div>
            </div>
          )}

          {/* 대안 */}
          {result.alternatives.length > 0 && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="text-xs font-semibold text-green-700 mb-2">대안 정보</h4>
              {result.alternatives.map((alt, i) => (
                <div key={i} className="text-sm text-gray-700">
                  <span className="font-medium">{String(alt.material || alt.equipment || '')}</span>
                  {alt.current_suppliers && (
                    <span className="text-xs text-gray-500 ml-2">공급처: {String(alt.current_suppliers)}</span>
                  )}
                  {alt.geographic_concentration && (
                    <span className="text-xs text-gray-500 ml-2">집중도: {String(alt.geographic_concentration)}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
