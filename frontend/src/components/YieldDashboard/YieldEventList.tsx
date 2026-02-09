/**
 * Yield Event List Component
 * 수율 이벤트 목록
 */

import type { YieldEvent } from '../../types/yield';
import GraphContextPanel from './GraphContextPanel';

interface Props {
  events: YieldEvent[];
  onAnalyze: (event: YieldEvent) => void;
  selectedEventId?: string;
  onNavigateToGraph?: (query?: string) => void;
}

export default function YieldEventList({ events, onAnalyze, selectedEventId, onNavigateToGraph }: Props) {
  if (!events || events.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-400">
        최근 이벤트가 없습니다
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      OPEN: 'bg-red-900/30 text-red-400',
      INVESTIGATING: 'bg-yellow-900/30 text-yellow-400',
      ROOT_CAUSE_IDENTIFIED: 'bg-blue-900/30 text-blue-400',
      RESOLVED: 'bg-green-900/30 text-green-400',
      CLOSED: 'bg-gray-800 text-gray-400',
    };

    const labels: Record<string, string> = {
      OPEN: '신규',
      INVESTIGATING: '분석중',
      ROOT_CAUSE_IDENTIFIED: '원인파악',
      RESOLVED: '해결됨',
      CLOSED: '종료',
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.OPEN}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getSeverityIndicator = (severity: string) => {
    const colors: Record<string, string> = {
      CRITICAL: 'bg-red-500',
      HIGH: 'bg-orange-500',
      MEDIUM: 'bg-yellow-500',
      LOW: 'bg-blue-500',
    };

    return <span className={`w-2 h-2 rounded-full ${colors[severity] || colors.LOW}`} />;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-3 max-h-96 overflow-y-auto">
      {events.map((event) => (
        <div
          key={event.event_id}
          className={`p-4 rounded-lg border transition cursor-pointer ${
            selectedEventId === event.event_id
              ? 'border-nexus-500 bg-nexus-900/20'
              : 'border-gray-700 hover:border-nexus-600 hover:bg-[#1E2433]'
          }`}
          onClick={() => onAnalyze(event)}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2">
              {getSeverityIndicator(event.severity)}
              <span className="font-medium text-gray-100 text-sm">{event.title}</span>
            </div>
            {getStatusBadge(event.status)}
          </div>

          <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
            <span>수율 저하: -{event.yield_drop_percent.toFixed(1)}%</span>
            <span>{formatDate(event.detected_at)}</span>
            {event.affected_wafer_count && (
              <span>영향: {event.affected_wafer_count} 웨이퍼</span>
            )}
          </div>

          {event.analysis_summary && (
            <p className="mt-2 text-xs text-gray-400 line-clamp-2">
              {event.analysis_summary}
            </p>
          )}

          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAnalyze(event);
              }}
              className="px-3 py-1 text-xs font-medium text-nexus-400 bg-nexus-900/20 rounded hover:bg-nexus-900/40 transition"
            >
              RCA 분석
            </button>
            {event.root_causes && event.root_causes.length > 0 && (
              <span className="text-xs text-green-600">
                ✓ {event.root_causes.length}개 원인 식별됨
              </span>
            )}
          </div>

          {/* 그래프 컨텍스트 패널 */}
          {selectedEventId === event.event_id && (
            <GraphContextPanel
              processStep={event.title}
              equipmentId={
                event.root_causes?.find(rc => rc.cause_type === 'EQUIPMENT')?.entity_id
              }
              onNavigateToGraph={onNavigateToGraph}
            />
          )}
        </div>
      ))}
    </div>
  );
}
