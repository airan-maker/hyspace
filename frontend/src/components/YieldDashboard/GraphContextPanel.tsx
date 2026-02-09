/**
 * Graph Context Panel
 * 수율 이벤트의 관련 그래프 노드를 표시하는 패널
 */

import { useState } from 'react';
import { getGraphContextForEvent, type GraphContextResult } from '../../services/api';

const LABEL_COLORS: Record<string, string> = {
  ProcessStep: '#6366f1',
  Equipment: '#10b981',
  Material: '#ef4444',
  DefectType: '#f59e0b',
  FailureMode: '#ec4899',
  ProcessNode: '#3b82f6',
};

interface Props {
  processStep?: string;
  equipmentId?: string;
  onNavigateToGraph?: (query?: string) => void;
}

export default function GraphContextPanel({ processStep, equipmentId, onNavigateToGraph }: Props) {
  const [result, setResult] = useState<GraphContextResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const fetchContext = async () => {
    if (!processStep && !equipmentId) return;

    setIsLoading(true);
    setError(null);
    try {
      const data = await getGraphContextForEvent({
        process_step: processStep,
        equipment_id: equipmentId,
      });
      setResult(data);
      setIsOpen(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || '그래프 컨텍스트 조회 실패');
    } finally {
      setIsLoading(false);
    }
  };

  if (!processStep && !equipmentId) return null;

  return (
    <div className="mt-3">
      {!isOpen ? (
        <button
          onClick={fetchContext}
          disabled={isLoading}
          className="flex items-center gap-2 px-3 py-1.5 text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg hover:bg-indigo-100 disabled:opacity-50 transition-colors"
        >
          {isLoading ? (
            <>
              <div className="animate-spin w-3 h-3 border-2 border-indigo-300 border-t-indigo-600 rounded-full" />
              조회 중...
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-4.486a4.5 4.5 0 00-6.364-6.364L5.265 6.264a4.5 4.5 0 001.242 7.244" />
              </svg>
              그래프 컨텍스트
            </>
          )}
        </button>
      ) : (
        <div className="bg-white border border-indigo-200 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-indigo-700">관련 그래프 노드</h4>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-gray-600 text-xs"
            >
              접기
            </button>
          </div>

          {error && (
            <p className="text-xs text-red-500 mb-2">{error}</p>
          )}

          {result && (
            <>
              {result.nodes.length === 0 ? (
                <p className="text-xs text-gray-500">관련 그래프 노드를 찾을 수 없습니다.</p>
              ) : (
                <div className="space-y-2">
                  {/* 노드 목록 */}
                  <div className="flex flex-wrap gap-1.5">
                    {result.nodes.map((node, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] rounded-full text-white"
                        style={{ backgroundColor: LABEL_COLORS[node.label] || '#6b7280' }}
                      >
                        {node.label}: {node.name}
                      </span>
                    ))}
                  </div>

                  {/* 관계 */}
                  {result.relationships.length > 0 && (
                    <div className="text-[10px] text-gray-500 space-y-0.5">
                      {result.relationships.slice(0, 5).map((rel, i) => (
                        <div key={i} className="font-mono">
                          {rel.from} <span className="text-indigo-500">→ {rel.type} →</span> {rel.to}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Graph Explorer 이동 버튼 */}
                  {onNavigateToGraph && (
                    <button
                      onClick={() => onNavigateToGraph(result.suggested_queries[0])}
                      className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors mt-1"
                    >
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      Graph Explorer에서 보기
                    </button>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
