import type { PPAResult } from '../../types';

interface PPAResultsProps {
  result: PPAResult | null;
  isLoading: boolean;
}

function MetricCard({ label, value, unit, subtext, color = 'nexus' }: {
  label: string;
  value: string | number;
  unit: string;
  subtext?: string;
  color?: 'nexus' | 'green' | 'yellow' | 'red';
}) {
  const colorClasses = {
    nexus: 'text-nexus-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold ${colorClasses[color]}`}>
        {value}<span className="text-lg font-normal ml-1">{unit}</span>
      </p>
      {subtext && <p className="text-xs text-gray-400 mt-1">{subtext}</p>}
    </div>
  );
}

function ConfidenceBadge({ score }: { score: number }) {
  let colorClass = 'badge-green';
  let label = 'High';

  if (score < 70) {
    colorClass = 'badge-red';
    label = 'Low';
  } else if (score < 90) {
    colorClass = 'badge-yellow';
    label = 'Medium';
  }

  return (
    <span className={`badge ${colorClass}`}>
      {label} Confidence ({score}%)
    </span>
  );
}

export function PPAResults({ result, isLoading }: PPAResultsProps) {
  if (isLoading) {
    return (
      <div className="card">
        <h2 className="card-header">PPA Analysis</h2>
        <div className="animate-pulse space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="card">
        <h2 className="card-header">PPA Analysis</h2>
        <p className="text-gray-500 text-center py-8">
          Configure your chip and run simulation to see results
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="card-header mb-0">PPA Analysis</h2>
        <ConfidenceBadge score={result.confidence_score} />
      </div>

      {/* Main Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <MetricCard
          label="Die Size"
          value={result.die_size_mm2.toFixed(1)}
          unit="mm²"
        />
        <MetricCard
          label="TDP"
          value={result.power_tdp_w.toFixed(1)}
          unit="W"
          color={result.power_tdp_w > 100 ? 'red' : result.power_tdp_w > 65 ? 'yellow' : 'green'}
        />
        <MetricCard
          label="Frequency"
          value={result.performance_ghz.toFixed(1)}
          unit="GHz"
        />
        <MetricCard
          label="AI Performance"
          value={result.performance_tops.toFixed(0)}
          unit="TOPS"
          subtext={`${result.efficiency_tops_per_watt.toFixed(2)} TOPS/W`}
        />
      </div>

      {/* Area Breakdown */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Area Breakdown</h3>
        <div className="space-y-2">
          {Object.entries(result.area_breakdown)
            .filter(([key]) => key !== 'total')
            .sort(([, a], [, b]) => b - a)
            .map(([key, value]) => (
              <div key={key} className="flex items-center gap-2">
                <span className="text-xs text-gray-500 w-24 capitalize">{key.replace('_', ' ')}</span>
                <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-nexus-500 rounded-full"
                    style={{ width: `${(value / result.area_breakdown.total) * 100}%` }}
                  />
                </div>
                <span className="text-xs font-medium text-gray-700 w-16 text-right">{value.toFixed(1)} mm²</span>
              </div>
            ))}
        </div>
      </div>

      {/* Power Breakdown */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">Power Breakdown</h3>
        <div className="space-y-2">
          {Object.entries(result.power_breakdown)
            .filter(([key]) => key !== 'total')
            .sort(([, a], [, b]) => b - a)
            .map(([key, value]) => (
              <div key={key} className="flex items-center gap-2">
                <span className="text-xs text-gray-500 w-24 capitalize">{key}</span>
                <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange-500 rounded-full"
                    style={{ width: `${(value / result.power_breakdown.total) * 100}%` }}
                  />
                </div>
                <span className="text-xs font-medium text-gray-700 w-12 text-right">{value.toFixed(1)} W</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
