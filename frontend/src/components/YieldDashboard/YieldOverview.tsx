/**
 * Yield Overview Component
 * 수율 개요 카드 컴포넌트
 */

import type { YieldDashboard } from '../../types/yield';

interface Props {
  dashboard: YieldDashboard;
}

export default function YieldOverview({ dashboard }: Props) {
  const {
    overall_yield,
    yield_target,
    yield_vs_target,
    active_events,
    critical_events,
    events_this_week,
  } = dashboard;

  const yieldStatus =
    yield_vs_target >= 0
      ? { color: 'text-green-600', bg: 'bg-green-100', icon: '↑' }
      : { color: 'text-red-600', bg: 'bg-red-100', icon: '↓' };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Overall Yield */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">전체 수율</p>
            <p className="text-3xl font-bold text-gray-900">
              {overall_yield.toFixed(1)}%
            </p>
          </div>
          <div
            className={`w-12 h-12 rounded-full ${yieldStatus.bg} flex items-center justify-center`}
          >
            <span className={`text-xl font-bold ${yieldStatus.color}`}>
              {yieldStatus.icon}
            </span>
          </div>
        </div>
        <div className="mt-4 flex items-center text-sm">
          <span className={yieldStatus.color}>
            {yield_vs_target >= 0 ? '+' : ''}
            {yield_vs_target.toFixed(1)}%
          </span>
          <span className="text-gray-500 ml-2">목표 대비 ({yield_target}%)</span>
        </div>
      </div>

      {/* Active Events */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">활성 이벤트</p>
            <p className="text-3xl font-bold text-gray-900">{active_events}</p>
          </div>
          <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
            <svg
              className="w-6 h-6 text-blue-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
        </div>
        <div className="mt-4 text-sm text-gray-500">
          분석 중인 수율 저하 이벤트
        </div>
      </div>

      {/* Critical Events */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">긴급 이벤트</p>
            <p className="text-3xl font-bold text-red-600">{critical_events}</p>
          </div>
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
            <svg
              className="w-6 h-6 text-red-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
        </div>
        <div className="mt-4 text-sm text-gray-500">
          즉시 조치가 필요한 이벤트
        </div>
      </div>

      {/* Weekly Events */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">이번 주 이벤트</p>
            <p className="text-3xl font-bold text-gray-900">{events_this_week}</p>
          </div>
          <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
            <svg
              className="w-6 h-6 text-purple-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        </div>
        <div className="mt-4 text-sm text-gray-500">
          최근 7일간 발생한 이벤트
        </div>
      </div>
    </div>
  );
}
