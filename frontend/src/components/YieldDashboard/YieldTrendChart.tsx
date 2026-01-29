/**
 * Yield Trend Chart Component
 * 수율 트렌드 차트 (간단한 SVG 기반)
 */

import type { YieldTrendPoint } from '../../types/yield';

interface Props {
  data: YieldTrendPoint[];
}

export default function YieldTrendChart({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        데이터가 없습니다
      </div>
    );
  }

  // 차트 계산
  const yields = data.map((d) => d.yield_percent);
  const minYield = Math.min(...yields) - 2;
  const maxYield = Math.max(...yields) + 2;
  const yieldRange = maxYield - minYield;

  const chartWidth = 100;
  const chartHeight = 60;
  const padding = 5;

  // 포인트 계산
  const points = data.map((d, i) => {
    const x = padding + (i / (data.length - 1)) * (chartWidth - 2 * padding);
    const y =
      chartHeight -
      padding -
      ((d.yield_percent - minYield) / yieldRange) * (chartHeight - 2 * padding);
    return { x, y, data: d };
  });

  // SVG path
  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  // 목표선 (92%)
  const targetY =
    chartHeight -
    padding -
    ((92 - minYield) / yieldRange) * (chartHeight - 2 * padding);

  return (
    <div className="space-y-4">
      {/* Chart */}
      <div className="relative h-64">
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="w-full h-full"
          preserveAspectRatio="none"
        >
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map((percent) => {
            const y =
              chartHeight -
              padding -
              (percent / 100) * (chartHeight - 2 * padding);
            return (
              <line
                key={percent}
                x1={padding}
                y1={y}
                x2={chartWidth - padding}
                y2={y}
                stroke="#e5e7eb"
                strokeWidth="0.5"
              />
            );
          })}

          {/* Target line */}
          <line
            x1={padding}
            y1={targetY}
            x2={chartWidth - padding}
            y2={targetY}
            stroke="#ef4444"
            strokeWidth="0.5"
            strokeDasharray="2,2"
          />

          {/* Area fill */}
          <path
            d={`${linePath} L ${points[points.length - 1].x} ${chartHeight - padding} L ${points[0].x} ${chartHeight - padding} Z`}
            fill="url(#yieldGradient)"
            opacity="0.3"
          />

          {/* Line */}
          <path d={linePath} fill="none" stroke="#3b82f6" strokeWidth="1.5" />

          {/* Points */}
          {points.map((p, i) => (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r="1.5"
              fill="#3b82f6"
              className="hover:r-3 transition-all"
            />
          ))}

          {/* Gradient definition */}
          <defs>
            <linearGradient id="yieldGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>

        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-gray-500 py-2">
          <span>{maxYield.toFixed(0)}%</span>
          <span>{((maxYield + minYield) / 2).toFixed(0)}%</span>
          <span>{minYield.toFixed(0)}%</span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-blue-500"></div>
          <span className="text-gray-600">수율</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-red-500 border-dashed"></div>
          <span className="text-gray-600">목표 (92%)</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 text-center text-sm">
        <div>
          <p className="text-gray-500">평균</p>
          <p className="font-semibold text-gray-900">
            {(yields.reduce((a, b) => a + b, 0) / yields.length).toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-gray-500">최고</p>
          <p className="font-semibold text-green-600">{Math.max(...yields).toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-gray-500">최저</p>
          <p className="font-semibold text-red-600">{Math.min(...yields).toFixed(1)}%</p>
        </div>
      </div>
    </div>
  );
}
