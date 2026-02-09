import type {
  WorkloadAnalysisResult,
  RecommendedArchitecture,
} from '../../types/workload';

interface WorkloadResultsProps {
  result: WorkloadAnalysisResult | null;
  isLoading: boolean;
}

function CharacterizationBadge({ type, bottleneck }: { type: string; bottleneck: string }) {
  const colorMap: Record<string, string> = {
    'Memory-Bound': 'bg-purple-900/30 text-purple-400',
    'Compute-Bound': 'bg-blue-900/30 text-blue-400',
    'Balanced': 'bg-green-900/30 text-green-400',
  };

  return (
    <div className="flex flex-wrap gap-2">
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${colorMap[type] || 'bg-gray-800 text-gray-300'}`}>
        {type}
      </span>
      <span className="px-3 py-1 rounded-full text-sm font-medium bg-orange-900/30 text-orange-400">
        Bottleneck: {bottleneck}
      </span>
    </div>
  );
}

function MetricRow({ label, value, unit }: { label: string; value: string | number; unit: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-700 last:border-0">
      <span className="text-sm text-gray-400">{label}</span>
      <span className="text-sm font-semibold text-gray-100">
        {value}<span className="text-gray-500 font-normal ml-1">{unit}</span>
      </span>
    </div>
  );
}

function ArchitectureCard({ arch, isRecommended }: { arch: RecommendedArchitecture; isRecommended: boolean }) {
  return (
    <div className={`rounded-lg border-2 p-4 ${isRecommended ? 'border-nexus-500 bg-nexus-900/20' : 'border-gray-700'}`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-semibold text-gray-100">{arch.name}</h4>
          <p className="text-xs text-gray-400">{arch.process_node_nm}nm Process</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {isRecommended && (
            <span className="px-2 py-0.5 bg-nexus-600 text-white text-xs font-medium rounded-full">
              Recommended
            </span>
          )}
          <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
            arch.match_score >= 90 ? 'bg-green-900/30 text-green-400' :
            arch.match_score >= 70 ? 'bg-yellow-900/30 text-yellow-400' :
            'bg-red-900/30 text-red-400'
          }`}>
            {arch.match_score}% Match
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 mb-3">
        <MetricRow label="NPU Cores" value={arch.npu_cores} unit="" />
        <MetricRow label="Memory" value={arch.memory_capacity_gb} unit="GB" />
        <MetricRow label="Performance" value={arch.performance_tops.toLocaleString()} unit="TOPS" />
        <MetricRow label="TDP" value={arch.power_tdp_w} unit="W" />
        <MetricRow label="Efficiency" value={arch.efficiency_tops_per_watt.toFixed(1)} unit="TOPS/W" />
        <MetricRow label="Die Size" value={arch.die_size_mm2.toFixed(0)} unit="mm2" />
      </div>

      <div className="text-lg font-bold text-nexus-400 mb-3">
        Est. Unit Cost: ${arch.estimated_unit_cost.toFixed(0)}
      </div>

      {/* Justifications */}
      {arch.justifications.length > 0 && (
        <div className="mb-2">
          <p className="text-xs font-medium text-green-400 mb-1">Strengths:</p>
          <ul className="text-xs text-gray-400 space-y-0.5">
            {arch.justifications.slice(0, 3).map((j, i) => (
              <li key={i} className="flex items-start gap-1">
                <span className="text-green-500 mt-0.5">+</span>
                {j}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Trade-offs */}
      {arch.trade_offs.length > 0 && (
        <div>
          <p className="text-xs font-medium text-yellow-400 mb-1">Trade-offs:</p>
          <ul className="text-xs text-gray-400 space-y-0.5">
            {arch.trade_offs.slice(0, 2).map((t, i) => (
              <li key={i} className="flex items-start gap-1">
                <span className="text-yellow-500 mt-0.5">-</span>
                {t}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ConfidenceBadge({ score }: { score: number }) {
  let colorClass = 'bg-green-900/30 text-green-400';
  let label = 'High';

  if (score < 70) {
    colorClass = 'bg-red-900/30 text-red-400';
    label = 'Low';
  } else if (score < 90) {
    colorClass = 'bg-yellow-900/30 text-yellow-400';
    label = 'Medium';
  }

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${colorClass}`}>
      {label} Confidence ({score}%)
    </span>
  );
}

export function WorkloadResults({ result, isLoading }: WorkloadResultsProps) {
  if (isLoading) {
    return (
      <div className="card">
        <h2 className="card-header">Workload Analysis</h2>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-700 rounded w-1/2" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2].map((i) => (
              <div key={i} className="h-64 bg-gray-700 rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="card">
        <h2 className="card-header">Workload Analysis</h2>
        <div className="text-center py-12">
          <svg className="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
          <p className="text-gray-400">Configure your workload profile and run analysis to see recommendations</p>
        </div>
      </div>
    );
  }

  const recommendedArch = result.recommended_architectures.find(a => a.is_recommended);
  const otherArchs = result.recommended_architectures.filter(a => !a.is_recommended);

  return (
    <div className="space-y-6">
      {/* Characterization Card */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="card-header mb-0">Workload Characterization</h2>
          <ConfidenceBadge score={result.confidence_score} />
        </div>

        <div className="mb-4">
          <CharacterizationBadge
            type={result.characterization.compute_intensity}
            bottleneck={result.characterization.bottleneck}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-[#1E2433] rounded-lg p-4">
            <p className="text-xs text-gray-400 uppercase tracking-wider">Required TOPS</p>
            <p className="text-2xl font-bold text-nexus-600">
              {result.characterization.required_tops.toLocaleString()}
            </p>
          </div>
          <div className="bg-[#1E2433] rounded-lg p-4">
            <p className="text-xs text-gray-400 uppercase tracking-wider">Arithmetic Intensity</p>
            <p className="text-2xl font-bold text-purple-600">
              {result.characterization.arithmetic_intensity.toFixed(1)} <span className="text-lg font-normal">OPs/B</span>
            </p>
          </div>
        </div>

        {result.analysis_notes.length > 0 && (
          <div className="mt-4 p-3 bg-blue-900/20 rounded-lg">
            <p className="text-sm font-medium text-blue-300 mb-2">Analysis Notes</p>
            <ul className="text-sm text-blue-400 space-y-1">
              {result.analysis_notes.map((note, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-blue-500">*</span>
                  {note}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Recommended Architecture */}
      {recommendedArch && (
        <div className="card">
          <h2 className="card-header flex items-center gap-2">
            <svg className="w-5 h-5 text-nexus-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Recommended Architecture
          </h2>
          <ArchitectureCard arch={recommendedArch} isRecommended={true} />
        </div>
      )}

      {/* Alternative Architectures */}
      {otherArchs.length > 0 && (
        <div className="card">
          <h2 className="card-header">Alternative Options</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {otherArchs.map((arch, i) => (
              <ArchitectureCard key={i} arch={arch} isRecommended={false} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
