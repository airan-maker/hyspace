/**
 * RCA Panel Component
 * 근본 원인 분석 결과 패널
 */

import type { YieldEvent, RCAResponse, RootCause } from '../../types/yield';

interface Props {
  event: YieldEvent | null;
  result: RCAResponse | null;
  isLoading: boolean;
}

export default function RCAPanel({ event, result, isLoading }: Props) {
  if (!event) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-gray-400">
        <svg
          className="w-12 h-12 text-gray-400 mb-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
          />
        </svg>
        <p>이벤트를 선택하여 근본 원인 분석을 실행하세요</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="h-64 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-4"></div>
        <p className="text-gray-400">근본 원인 분석 중...</p>
        <p className="text-sm text-gray-400 mt-2">{event.title}</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-400">
        분석 결과가 없습니다
      </div>
    );
  }

  const getCauseTypeLabel = (type: string) => {
    const labels: Record<string, { text: string; color: string; icon: string }> = {
      EQUIPMENT: { text: '장비', color: 'bg-purple-900/30 text-purple-400', icon: '⚙️' },
      MATERIAL: { text: '재료', color: 'bg-green-900/30 text-green-400', icon: '🧪' },
      PROCESS: { text: '공정', color: 'bg-blue-900/30 text-blue-400', icon: '🔧' },
      HUMAN: { text: '인적', color: 'bg-orange-900/30 text-orange-400', icon: '👤' },
      ENVIRONMENT: { text: '환경', color: 'bg-cyan-900/30 text-cyan-400', icon: '🌡️' },
      UNKNOWN: { text: '미상', color: 'bg-gray-800 text-gray-400', icon: '❓' },
    };
    return labels[type] || labels.UNKNOWN;
  };

  const getProbabilityColor = (prob: number) => {
    if (prob >= 80) return 'text-red-600';
    if (prob >= 60) return 'text-orange-600';
    if (prob >= 40) return 'text-yellow-600';
    return 'text-gray-400';
  };

  return (
    <div className="space-y-4 max-h-[500px] overflow-y-auto">
      {/* Event Info */}
      <div className="p-3 bg-[#1E2433] rounded-lg">
        <div className="flex items-center justify-between">
          <span className="font-medium text-gray-100">{event.title}</span>
          <span className="text-sm text-gray-400">{event.event_id}</span>
        </div>
        <div className="mt-1 flex items-center gap-3 text-sm text-gray-400">
          <span>수율 저하: -{event.yield_drop_percent.toFixed(1)}%</span>
          <span>•</span>
          <span>분석 신뢰도: {result.confidence_score.toFixed(1)}%</span>
        </div>
      </div>

      {/* Root Causes */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">
          식별된 원인 ({result.root_causes.length}개)
        </h3>
        <div className="space-y-3">
          {result.root_causes.map((cause, idx) => {
            const typeInfo = getCauseTypeLabel(cause.cause_type);
            return (
              <div
                key={idx}
                className="p-3 border border-gray-700 rounded-lg hover:border-nexus-600 transition"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{typeInfo.icon}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${typeInfo.color}`}
                    >
                      {typeInfo.text}
                    </span>
                    <span className="font-medium text-gray-100 text-sm">
                      {cause.entity_id}
                    </span>
                  </div>
                  <span
                    className={`font-bold text-lg ${getProbabilityColor(cause.probability)}`}
                  >
                    {cause.probability.toFixed(0)}%
                  </span>
                </div>

                <p className="mt-2 text-sm text-gray-400">{cause.description}</p>

                {cause.evidence && cause.evidence.length > 0 && (
                  <div className="mt-2 pl-3 border-l-2 border-gray-700">
                    <p className="text-xs text-gray-400 font-medium mb-1">근거:</p>
                    <ul className="text-xs text-gray-400 space-y-0.5">
                      {cause.evidence.map((e, i) => (
                        <li key={i}>• {e}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Recommendations */}
      {result.recommendations && result.recommendations.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-3">권장 조치</h3>
          <ul className="space-y-2">
            {result.recommendations.map((rec, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 p-2 bg-blue-900/20 rounded text-sm text-blue-400"
              >
                <span className="text-blue-500 mt-0.5">→</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Similar Events */}
      {result.similar_events && result.similar_events.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">유사 이벤트</h3>
          <div className="flex flex-wrap gap-2">
            {result.similar_events.map((eventId, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-gray-800 text-gray-400 rounded text-xs"
              >
                {eventId}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Analysis Metadata */}
      <div className="pt-3 border-t border-gray-700 text-xs text-gray-400">
        <div className="flex justify-between">
          <span>분석 방법: {result.analysis_method}</span>
          <span>분석 시간: {result.analysis_time_seconds.toFixed(2)}초</span>
        </div>
      </div>
    </div>
  );
}
