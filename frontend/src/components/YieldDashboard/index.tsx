/**
 * Yield Dashboard Component
 * 수율 대시보드 메인 컴포넌트
 */

import { useState, useEffect } from 'react';
import { getYieldDashboard, getYieldEvents, analyzeRootCause } from '../../services/yieldApi';
import type { YieldDashboard, YieldEvent, RCAResponse } from '../../types/yield';
import YieldOverview from './YieldOverview';
import YieldTrendChart from './YieldTrendChart';
import EquipmentYieldTable from './EquipmentYieldTable';
import YieldEventList from './YieldEventList';
import RCAPanel from './RCAPanel';

export default function YieldDashboardPage({ onNavigateToGraph }: { onNavigateToGraph?: () => void } = {}) {
  const [dashboard, setDashboard] = useState<YieldDashboard | null>(null);
  const [events, setEvents] = useState<YieldEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<YieldEvent | null>(null);
  const [rcaResult, setRcaResult] = useState<RCAResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [periodDays, setPeriodDays] = useState(30);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, [periodDays]);

  async function loadDashboard() {
    setIsLoading(true);
    setError(null);
    try {
      const [dashboardData, eventsData] = await Promise.all([
        getYieldDashboard(periodDays),
        getYieldEvents(undefined, undefined, undefined, undefined, 10),
      ]);
      setDashboard(dashboardData);
      setEvents(eventsData);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError('대시보드 데이터를 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleAnalyzeEvent(event: YieldEvent) {
    setSelectedEvent(event);
    setIsAnalyzing(true);
    setRcaResult(null);
    try {
      const result = await analyzeRootCause(event.event_id, 3, true, 48);
      setRcaResult(result);
    } catch (err) {
      console.error('RCA failed:', err);
      setError('근본 원인 분석에 실패했습니다.');
    } finally {
      setIsAnalyzing(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-nexus-500"></div>
        <span className="ml-3 text-gray-400">데이터 로딩 중...</span>
      </div>
    );
  }

  if (error && !dashboard) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-red-400">
        {error}
        <button
          onClick={loadDashboard}
          className="ml-4 text-red-400 underline hover:text-red-300"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">수율 대시보드</h1>
          <p className="text-gray-400">실시간 수율 모니터링 및 근본 원인 분석</p>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(Number(e.target.value))}
            className="px-3 py-2 border border-gray-600 bg-[#111420] rounded-lg focus:ring-2 focus:ring-nexus-500"
          >
            <option value={7}>최근 7일</option>
            <option value={30}>최근 30일</option>
            <option value={90}>최근 90일</option>
          </select>
          <button
            onClick={loadDashboard}
            className="px-4 py-2 bg-nexus-600 text-white rounded-lg hover:bg-nexus-700 transition"
          >
            새로고침
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      {dashboard && <YieldOverview dashboard={dashboard} />}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Yield Trend Chart */}
        <div className="bg-[#161B28] rounded-xl shadow-sm border border-gray-700/50 p-6">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">수율 트렌드</h2>
          {dashboard && <YieldTrendChart data={dashboard.trend_data} />}
        </div>

        {/* Equipment Yield Table */}
        <div className="bg-[#161B28] rounded-xl shadow-sm border border-gray-700/50 p-6">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">장비별 수율</h2>
          {dashboard && <EquipmentYieldTable data={dashboard.by_equipment} />}
        </div>
      </div>

      {/* Events and RCA Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Events */}
        <div className="bg-[#161B28] rounded-xl shadow-sm border border-gray-700/50 p-6">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">최근 수율 이벤트</h2>
          <YieldEventList
            events={events}
            onAnalyze={handleAnalyzeEvent}
            selectedEventId={selectedEvent?.event_id}
            onNavigateToGraph={onNavigateToGraph}
          />
        </div>

        {/* RCA Panel */}
        <div className="bg-[#161B28] rounded-xl shadow-sm border border-gray-700/50 p-6">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">
            근본 원인 분석 (RCA)
          </h2>
          <RCAPanel
            event={selectedEvent}
            result={rcaResult}
            isLoading={isAnalyzing}
          />
        </div>
      </div>

      {/* Alerts Section */}
      {dashboard && dashboard.recent_alerts.length > 0 && (
        <div className="bg-[#161B28] rounded-xl shadow-sm border border-gray-700/50 p-6">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">최근 알림</h2>
          <div className="space-y-3">
            {dashboard.recent_alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`flex items-center p-3 rounded-lg ${
                  alert.severity === 'CRITICAL' || alert.severity === 'HIGH'
                    ? 'bg-red-900/20 border border-red-800'
                    : alert.severity === 'MEDIUM'
                    ? 'bg-yellow-900/20 border border-yellow-800'
                    : 'bg-blue-900/20 border border-blue-800'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full mr-3 ${
                    alert.severity === 'CRITICAL' || alert.severity === 'HIGH'
                      ? 'bg-red-500'
                      : alert.severity === 'MEDIUM'
                      ? 'bg-yellow-500'
                      : 'bg-blue-500'
                  }`}
                />
                <span className="flex-1 text-gray-300">{alert.message}</span>
                <span className="text-sm text-gray-500">{alert.time}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
