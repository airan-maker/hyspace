/**
 * Yield Event List Component
 * 수율 이벤트 목록
 */

import type { YieldEvent } from '../../types/yield';

interface Props {
  events: YieldEvent[];
  onAnalyze: (event: YieldEvent) => void;
  selectedEventId?: string;
}

export default function YieldEventList({ events, onAnalyze, selectedEventId }: Props) {
  if (!events || events.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        최근 이벤트가 없습니다
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      OPEN: 'bg-red-100 text-red-700',
      INVESTIGATING: 'bg-yellow-100 text-yellow-700',
      ROOT_CAUSE_IDENTIFIED: 'bg-blue-100 text-blue-700',
      RESOLVED: 'bg-green-100 text-green-700',
      CLOSED: 'bg-gray-100 text-gray-700',
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
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
          }`}
          onClick={() => onAnalyze(event)}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2">
              {getSeverityIndicator(event.severity)}
              <span className="font-medium text-gray-900 text-sm">{event.title}</span>
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
            <p className="mt-2 text-xs text-gray-600 line-clamp-2">
              {event.analysis_summary}
            </p>
          )}

          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAnalyze(event);
              }}
              className="px-3 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100 transition"
            >
              RCA 분석
            </button>
            {event.root_causes && event.root_causes.length > 0 && (
              <span className="text-xs text-green-600">
                ✓ {event.root_causes.length}개 원인 식별됨
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
