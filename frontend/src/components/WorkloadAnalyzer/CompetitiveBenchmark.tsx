import type { CompetitiveBenchmark as BenchmarkType } from '../../types/workload';

interface CompetitiveBenchmarkProps {
  benchmarks: BenchmarkType[];
  ourArchName?: string;
  ourTops?: number;
  ourPower?: number;
  ourPrice?: number;
}

interface ProductRow {
  name: string;
  performance_tops: number;
  power_w: number;
  memory_bandwidth_tbps: number;
  estimated_price: number;
  efficiency: number;
  isOurs: boolean;
}

function MetricCell({ value, best, format = 'number' }: {
  value: number;
  best: boolean;
  format?: 'number' | 'currency' | 'watts'
}) {
  const formatValue = () => {
    switch (format) {
      case 'currency':
        return `$${value.toLocaleString()}`;
      case 'watts':
        return `${value}W`;
      default:
        return value.toLocaleString();
    }
  };

  return (
    <td className={`px-4 py-3 text-sm text-right ${best ? 'font-bold text-nexus-400' : 'text-gray-300'}`}>
      {formatValue()}
      {best && <span className="ml-1 text-green-500">*</span>}
    </td>
  );
}

export function CompetitiveBenchmark({
  benchmarks,
  ourArchName = 'Our Design',
  ourTops,
  ourPower,
  ourPrice,
}: CompetitiveBenchmarkProps) {
  if (!benchmarks || benchmarks.length === 0) {
    return null;
  }

  // Convert benchmarks to a common format and add our architecture if provided
  const allProducts: ProductRow[] = [];

  if (ourTops && ourPower && ourPrice) {
    allProducts.push({
      name: ourArchName,
      performance_tops: ourTops,
      power_w: ourPower,
      memory_bandwidth_tbps: 0,
      estimated_price: ourPrice,
      efficiency: ourTops / ourPower,
      isOurs: true,
    });
  }

  benchmarks.forEach(b => {
    allProducts.push({
      name: b.competitor_name,
      performance_tops: b.performance_tops,
      power_w: b.power_tdp_w,
      memory_bandwidth_tbps: b.memory_bandwidth_tbps,
      estimated_price: b.estimated_price,
      efficiency: b.performance_tops / b.power_tdp_w,
      isOurs: false,
    });
  });

  // Find best values
  const bestTops = Math.max(...allProducts.map(p => p.performance_tops));
  const bestPower = Math.min(...allProducts.map(p => p.power_w));
  const bestEfficiency = Math.max(...allProducts.map(p => p.efficiency));
  const bestPrice = Math.min(...allProducts.filter(p => p.estimated_price > 0).map(p => p.estimated_price));
  const bestBandwidth = Math.max(...allProducts.filter(p => !p.isOurs).map(p => p.memory_bandwidth_tbps));

  return (
    <div className="card">
      <h2 className="card-header flex items-center gap-2">
        <svg className="w-5 h-5 text-nexus-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        Competitive Benchmark
      </h2>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-[#1E2433]">
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Product
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                TOPS
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Power
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Efficiency
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Bandwidth
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Est. Price
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {allProducts.map((product, i) => (
              <tr
                key={i}
                className={product.isOurs ? 'bg-nexus-900/20' : (i % 2 === 0 ? 'bg-transparent' : 'bg-[#1E2433]/20')}
              >
                <td className={`px-4 py-3 text-sm font-medium ${product.isOurs ? 'text-nexus-400' : 'text-gray-100'}`}>
                  {product.name}
                  {product.isOurs && (
                    <span className="ml-2 px-2 py-0.5 bg-nexus-600 text-white text-xs rounded-full">
                      Ours
                    </span>
                  )}
                </td>
                <MetricCell
                  value={product.performance_tops}
                  best={product.performance_tops === bestTops}
                />
                <MetricCell
                  value={product.power_w}
                  best={product.power_w === bestPower}
                  format="watts"
                />
                <td className={`px-4 py-3 text-sm text-right ${
                  product.efficiency === bestEfficiency ? 'font-bold text-nexus-400' : 'text-gray-300'
                }`}>
                  {product.efficiency.toFixed(1)} T/W
                  {product.efficiency === bestEfficiency && <span className="ml-1 text-green-500">*</span>}
                </td>
                <td className={`px-4 py-3 text-sm text-right ${
                  !product.isOurs && product.memory_bandwidth_tbps === bestBandwidth ? 'font-bold text-nexus-400' : 'text-gray-300'
                }`}>
                  {product.isOurs ? '-' : `${product.memory_bandwidth_tbps.toFixed(1)} TB/s`}
                  {!product.isOurs && product.memory_bandwidth_tbps === bestBandwidth && <span className="ml-1 text-green-500">*</span>}
                </td>
                <MetricCell
                  value={product.estimated_price}
                  best={product.estimated_price === bestPrice && product.estimated_price > 0}
                  format="currency"
                />
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 text-xs text-gray-400">
        <span className="text-green-500">*</span> Best in category. Competitor data from public specifications.
      </div>

      {/* Summary Comparison */}
      {ourTops && ourPower && ourPrice && (
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="p-3 bg-[#1E2433] rounded-lg">
            <p className="text-xs text-gray-400 mb-1">vs H100 (Performance)</p>
            <p className={`text-lg font-bold ${ourTops / 3958 >= 1 ? 'text-green-600' : 'text-yellow-600'}`}>
              {((ourTops / 3958) * 100).toFixed(0)}%
            </p>
          </div>
          <div className="p-3 bg-[#1E2433] rounded-lg">
            <p className="text-xs text-gray-400 mb-1">vs H100 (Efficiency)</p>
            <p className={`text-lg font-bold ${(ourTops/ourPower) / 5.65 >= 1 ? 'text-green-600' : 'text-yellow-600'}`}>
              {(((ourTops/ourPower) / 5.65) * 100).toFixed(0)}%
            </p>
          </div>
          <div className="p-3 bg-[#1E2433] rounded-lg">
            <p className="text-xs text-gray-400 mb-1">vs H100 (Cost)</p>
            <p className="text-lg font-bold text-green-600">
              {((ourPrice / 30000) * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
