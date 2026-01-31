import { useState } from 'react';
import { Layout, type PageType } from './components/Layout';
import { ConfigPanel, PPAResults } from './components/PPAOptimizer';
import { CostPanel } from './components/CostAnalysis';
import { AlternativesComparison } from './components/Charts';
import { WorkloadInputPanel, WorkloadResults, CompetitiveBenchmark } from './components/WorkloadAnalyzer';
import YieldDashboardPage from './components/YieldDashboard';
import { useSimulation } from './hooks/useSimulation';
import { useWorkloadAnalysis } from './hooks/useWorkloadAnalysis';
import { SeedDataWizard } from './components/SeedDataWizard';

function PPAOptimizerPage() {
  const {
    config,
    volume,
    targetASP,
    ppaResult,
    costResult,
    alternatives,
    updateConfig,
    setVolume,
    setTargetASP,
    runSimulation,
    isPPALoading,
    isCostLoading,
  } = useSimulation();

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">PPA & Cost Optimizer</h1>
        <p className="text-gray-500 mt-1">
          Configure your chip architecture and analyze power, performance, area trade-offs with manufacturing costs.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Configuration */}
        <div className="lg:col-span-1">
          <ConfigPanel
            config={config}
            onConfigChange={updateConfig}
            onSimulate={runSimulation}
            isLoading={isPPALoading}
          />
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <PPAResults result={ppaResult} isLoading={isPPALoading} />
            <CostPanel
              result={costResult}
              volume={volume}
              targetASP={targetASP}
              onVolumeChange={setVolume}
              onTargetASPChange={setTargetASP}
              isLoading={isCostLoading}
            />
          </div>

          <AlternativesComparison alternatives={alternatives} />
        </div>
      </div>
    </>
  );
}

function WorkloadAnalyzerPage() {
  const {
    profile,
    result,
    presets,
    selectedPresetId,
    updateProfile,
    updateComputeRequirements,
    updateMemoryRequirements,
    updatePowerConstraints,
    updateDeploymentContext,
    runAnalysis,
    loadPreset,
    isLoading,
    isPresetsLoading,
  } = useWorkloadAnalysis();

  const recommendedArch = result?.recommended_architectures.find(a => a.is_recommended);

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Workload Analyzer</h1>
        <p className="text-gray-500 mt-1">
          Define your workload requirements and get optimized chip architecture recommendations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Input Panel */}
        <div className="lg:col-span-1">
          <WorkloadInputPanel
            profile={profile}
            presets={presets}
            selectedPresetId={selectedPresetId}
            onProfileChange={updateProfile}
            onComputeChange={updateComputeRequirements}
            onMemoryChange={updateMemoryRequirements}
            onPowerChange={updatePowerConstraints}
            onDeploymentChange={updateDeploymentContext}
            onPresetSelect={loadPreset}
            onAnalyze={runAnalysis}
            isLoading={isLoading}
            isPresetsLoading={isPresetsLoading}
          />
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-2 space-y-6">
          <WorkloadResults
            result={result}
            isLoading={isLoading}
          />

          {result && result.competitive_benchmarks.length > 0 && (
            <CompetitiveBenchmark
              benchmarks={result.competitive_benchmarks}
              ourArchName={recommendedArch?.name}
              ourTops={recommendedArch?.performance_tops}
              ourPower={recommendedArch?.power_tdp_w}
              ourPrice={recommendedArch?.estimated_unit_cost}
            />
          )}
        </div>
      </div>
    </>
  );
}

function HistoryPage() {
  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Simulation History</h1>
        <p className="text-gray-500 mt-1">
          View and compare your past simulations.
        </p>
      </div>

      <div className="card">
        <div className="text-center py-12">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-gray-500">Simulation history will be available soon</p>
        </div>
      </div>
    </>
  );
}

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('ppa');

  const renderPage = () => {
    switch (currentPage) {
      case 'ppa':
        return <PPAOptimizerPage />;
      case 'workload':
        return <WorkloadAnalyzerPage />;
      case 'yield':
        return <YieldDashboardPage />;
      case 'seed':
        return <SeedDataWizard />;
      case 'history':
        return <HistoryPage />;
      default:
        return <PPAOptimizerPage />;
    }
  };

  return (
    <Layout currentPage={currentPage} onPageChange={setCurrentPage}>
      {renderPage()}
    </Layout>
  );
}

export default App;
