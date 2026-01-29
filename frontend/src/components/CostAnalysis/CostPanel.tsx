import type { CostResult } from '../../types';

interface CostPanelProps {
  result: CostResult | null;
  volume: number;
  targetASP: number;
  onVolumeChange: (volume: number) => void;
  onTargetASPChange: (asp: number) => void;
  isLoading: boolean;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

export function CostPanel({
  result,
  volume,
  targetASP,
  onVolumeChange,
  onTargetASPChange,
  isLoading,
}: CostPanelProps) {
  const marginColor = result
    ? result.gross_margin_percent >= 40
      ? 'text-green-600'
      : result.gross_margin_percent >= 25
      ? 'text-yellow-600'
      : 'text-red-600'
    : 'text-gray-500';

  return (
    <div className="card">
      <h2 className="card-header flex items-center gap-2">
        <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Cost Analysis
      </h2>

      {/* Volume & ASP Inputs */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-2">
            Annual Volume
          </label>
          <select
            value={volume}
            onChange={(e) => onVolumeChange(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nexus-500 focus:border-nexus-500"
          >
            <option value={10000}>10,000</option>
            <option value={50000}>50,000</option>
            <option value={100000}>100,000</option>
            <option value={500000}>500,000</option>
            <option value={1000000}>1,000,000</option>
          </select>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-2">
            Target ASP ($)
          </label>
          <input
            type="number"
            value={targetASP}
            onChange={(e) => onTargetASPChange(Number(e.target.value))}
            min={10}
            max={1000}
            step={5}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-nexus-500 focus:border-nexus-500"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="animate-pulse space-y-4">
          <div className="h-20 bg-gray-200 rounded-lg" />
          <div className="h-48 bg-gray-200 rounded-lg" />
        </div>
      ) : result ? (
        <>
          {/* Gross Margin Highlight */}
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-6 mb-6 text-center">
            <p className="text-sm text-gray-500 mb-1">Gross Margin</p>
            <p className={`text-4xl font-bold ${marginColor}`}>
              {result.gross_margin_percent.toFixed(1)}%
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {formatCurrency(result.gross_margin)} per unit
            </p>
          </div>

          {/* Cost Breakdown Table */}
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-500">Wafer Cost</span>
              <span className="text-sm font-medium">{formatCurrency(result.wafer_cost)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-500">Die Cost (raw)</span>
              <span className="text-sm font-medium">{formatCurrency(result.die_cost)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-500">Good Die Cost (yield adjusted)</span>
              <span className="text-sm font-medium">{formatCurrency(result.good_die_cost)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-500">Package Cost</span>
              <span className="text-sm font-medium">{formatCurrency(result.package_cost)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-500">Test Cost</span>
              <span className="text-sm font-medium">{formatCurrency(result.test_cost)}</span>
            </div>
            <div className="flex justify-between py-2 bg-nexus-50 rounded-lg px-3 -mx-3">
              <span className="text-sm font-semibold text-nexus-700">Total Unit Cost</span>
              <span className="text-sm font-bold text-nexus-700">{formatCurrency(result.total_unit_cost)}</span>
            </div>
          </div>

          {/* Additional Metrics */}
          <div className="grid grid-cols-2 gap-4 mt-6">
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500">Net Die/Wafer</p>
              <p className="text-lg font-bold text-gray-900">{formatNumber(result.net_die_per_wafer)}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500">Yield Rate</p>
              <p className="text-lg font-bold text-gray-900">{result.yield_rate.toFixed(1)}%</p>
            </div>
          </div>
        </>
      ) : (
        <p className="text-gray-500 text-center py-8">
          Run simulation to see cost analysis
        </p>
      )}
    </div>
  );
}
