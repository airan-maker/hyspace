/**
 * Equipment Yield Table Component
 * 장비별 수율 테이블
 */

import type { YieldByEquipment } from '../../types/yield';

interface Props {
  data: YieldByEquipment[];
}

export default function EquipmentYieldTable({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-400">
        데이터가 없습니다
      </div>
    );
  }

  // 수율 기준 정렬 (낮은 수율 우선)
  const sortedData = [...data].sort((a, b) => a.avg_yield - b.avg_yield);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'UP':
        return <span className="text-green-400">↑</span>;
      case 'DOWN':
        return <span className="text-red-400">↓</span>;
      default:
        return <span className="text-gray-400">→</span>;
    }
  };

  const getYieldColor = (yield_percent: number) => {
    if (yield_percent >= 93) return 'text-green-400';
    if (yield_percent >= 90) return 'text-blue-400';
    if (yield_percent >= 85) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getYieldBgColor = (yield_percent: number) => {
    if (yield_percent >= 93) return 'bg-green-900/30';
    if (yield_percent >= 90) return 'bg-blue-900/30';
    if (yield_percent >= 85) return 'bg-yellow-900/30';
    return 'bg-red-900/30';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-left text-sm text-gray-400 border-b border-gray-700">
            <th className="pb-3 font-medium">장비</th>
            <th className="pb-3 font-medium">유형</th>
            <th className="pb-3 font-medium text-right">평균 수율</th>
            <th className="pb-3 font-medium text-right">웨이퍼 수</th>
            <th className="pb-3 font-medium text-center">추세</th>
          </tr>
        </thead>
        <tbody>
          {sortedData.map((equipment) => (
            <tr
              key={equipment.equipment_id}
              className="border-b border-gray-700/50 hover:bg-[#1E2433]"
            >
              <td className="py-3">
                <span className="font-medium text-gray-100">
                  {equipment.equipment_id}
                </span>
              </td>
              <td className="py-3">
                <span className="text-sm text-gray-400">{equipment.equipment_type}</span>
              </td>
              <td className="py-3 text-right">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium ${getYieldBgColor(
                    equipment.avg_yield
                  )} ${getYieldColor(equipment.avg_yield)}`}
                >
                  {equipment.avg_yield.toFixed(1)}%
                </span>
              </td>
              <td className="py-3 text-right text-gray-600">
                {equipment.wafer_count.toLocaleString()}
              </td>
              <td className="py-3 text-center text-lg">
                {getTrendIcon(equipment.trend)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-gray-700 flex justify-between text-sm">
        <div className="flex gap-4">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-green-900/30"></span>
            <span className="text-gray-400">우수 (≥93%)</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-yellow-900/30"></span>
            <span className="text-gray-400">주의 (85-90%)</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-900/30"></span>
            <span className="text-gray-400">경고 (&lt;85%)</span>
          </span>
        </div>
        <span className="text-gray-500">총 {data.length}개 장비</span>
      </div>
    </div>
  );
}
