import type { PPAAlternative } from '../../types';

interface AlternativesComparisonProps {
  alternatives: PPAAlternative[];
}

function formatVariantName(variant: string): string {
  const names: Record<string, string> = {
    current: 'Current',
    low_power: 'Low Power',
    high_performance: 'High Performance',
  };
  return names[variant] || variant;
}

function getVariantIcon(variant: string): React.ReactNode {
  switch (variant) {
    case 'current':
      return (
        <svg className="w-5 h-5 text-nexus-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case 'low_power':
      return (
        <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
        </svg>
      );
    case 'high_performance':
      return (
        <svg className="w-5 h-5 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      );
    default:
      return null;
  }
}

function getVariantColor(variant: string): string {
  switch (variant) {
    case 'current':
      return 'border-nexus-200 bg-nexus-50';
    case 'low_power':
      return 'border-green-200 bg-green-50';
    case 'high_performance':
      return 'border-orange-200 bg-orange-50';
    default:
      return 'border-gray-200 bg-gray-50';
  }
}

export function AlternativesComparison({ alternatives }: AlternativesComparisonProps) {
  if (alternatives.length === 0) {
    return null;
  }

  return (
    <div className="card">
      <h2 className="card-header flex items-center gap-2">
        <svg className="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        Configuration Alternatives
      </h2>

      <div className="grid grid-cols-3 gap-4">
        {alternatives.map(({ variant, result }) => (
          <div
            key={variant}
            className={`rounded-xl border-2 p-4 ${getVariantColor(variant)} ${
              variant === 'current' ? 'ring-2 ring-nexus-500' : ''
            }`}
          >
            <div className="flex items-center gap-2 mb-3">
              {getVariantIcon(variant)}
              <span className="font-semibold text-gray-900">
                {formatVariantName(variant)}
              </span>
              {variant === 'current' && (
                <span className="badge badge-green text-xs">Selected</span>
              )}
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Die Size</span>
                <span className="font-medium">{result.die_size_mm2.toFixed(1)} mm²</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Power</span>
                <span className="font-medium">{result.power_tdp_w.toFixed(1)} W</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Frequency</span>
                <span className="font-medium">{result.performance_ghz.toFixed(1)} GHz</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">AI TOPS</span>
                <span className="font-medium">{result.performance_tops.toFixed(0)}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-gray-200">
                <span className="text-gray-500">Efficiency</span>
                <span className="font-semibold text-nexus-600">
                  {result.efficiency_tops_per_watt.toFixed(2)} TOPS/W
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Comparison Table */}
      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 font-medium text-gray-500">Metric</th>
              {alternatives.map(({ variant }) => (
                <th key={variant} className="text-right py-2 font-medium text-gray-500">
                  {formatVariantName(variant)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-gray-100">
              <td className="py-2 text-gray-600">Die Size (mm²)</td>
              {alternatives.map(({ variant, result }) => (
                <td key={variant} className="py-2 text-right font-medium">
                  {result.die_size_mm2.toFixed(1)}
                </td>
              ))}
            </tr>
            <tr className="border-b border-gray-100">
              <td className="py-2 text-gray-600">TDP (W)</td>
              {alternatives.map(({ variant, result }) => (
                <td key={variant} className="py-2 text-right font-medium">
                  {result.power_tdp_w.toFixed(1)}
                </td>
              ))}
            </tr>
            <tr className="border-b border-gray-100">
              <td className="py-2 text-gray-600">Frequency (GHz)</td>
              {alternatives.map(({ variant, result }) => (
                <td key={variant} className="py-2 text-right font-medium">
                  {result.performance_ghz.toFixed(1)}
                </td>
              ))}
            </tr>
            <tr className="border-b border-gray-100">
              <td className="py-2 text-gray-600">AI Performance (TOPS)</td>
              {alternatives.map(({ variant, result }) => (
                <td key={variant} className="py-2 text-right font-medium">
                  {result.performance_tops.toFixed(0)}
                </td>
              ))}
            </tr>
            <tr>
              <td className="py-2 text-gray-600 font-medium">Efficiency (TOPS/W)</td>
              {alternatives.map(({ variant, result }) => (
                <td key={variant} className="py-2 text-right font-bold text-nexus-600">
                  {result.efficiency_tops_per_watt.toFixed(3)}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
