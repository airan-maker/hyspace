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
      <div className="h-64 flex items-center justify-center text-gray-500">
        데이터가 없습니다
      </div>
    );
  }

  // 수율 기준 정렬 (낮은 수율 우선)
  const sortedData = [...data].sort((a, b) => a.avg_yield - b.avg_yield);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'UP':
        return <span className="text-green-600">↑</span>;
      case 'DOWN':
        return <span className="text-red-600">↓</span>;
      default:
        return <span className="text-gray-400">→</span>;
    }
  };

  const getYieldColor = (yield_percent: number) => {
    if (yield_percent >= 93) return 'text-green-600';
    if (yield_percent >= 90) return 'text-blue-600';
    if (yield_percent >= 85) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getYieldBgColor = (yield_percent: number) => {
    if (yield_percent >= 93) return 'bg-green-100';
    if (yield_percent >= 90) return 'bg-blue-100';
    if (yield_percent >= 85) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-left text-sm text-gray-500 border-b border-gray-200">
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
              className="border-b border-gray-100 hover:bg-gray-50"
            >
              <td className="py-3">
                <span className="font-medium text-gray-900">
                  {equipment.equipment_id}
                </span>
              </td>
              <td className="py-3">
                <span className="text-sm text-gray-600">{equipment.equipment_type}</span>
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
      <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between text-sm">
        <div className="flex gap-4">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-green-100"></span>
            <span className="text-gray-600">우수 (≥93%)</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-yellow-100"></span>
            <span className="text-gray-600">주의 (85-90%)</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-100"></span>
            <span className="text-gray-600">경고 (&lt;85%)</span>
          </span>
        </div>
        <span className="text-gray-500">총 {data.length}개 장비</span>
      </div>
    </div>
  );
}
