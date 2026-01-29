import type { ChipConfig } from '../../types';

interface ConfigPanelProps {
  config: ChipConfig;
  onConfigChange: (updates: Partial<ChipConfig>) => void;
  onSimulate: () => void;
  isLoading: boolean;
}

interface SliderInputProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  onChange: (value: number) => void;
}

function SliderInput({ label, value, min, max, step = 1, unit = '', onChange }: SliderInputProps) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-sm font-semibold text-nexus-600">
          {value}{unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
      />
      <div className="flex justify-between text-xs text-gray-400">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}

export function ConfigPanel({ config, onConfigChange, onSimulate, isLoading }: ConfigPanelProps) {
  return (
    <div className="card">
      <h2 className="card-header flex items-center gap-2">
        <svg className="w-5 h-5 text-nexus-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Chip Configuration
      </h2>

      <div className="space-y-6">
        {/* Process Node Selection */}
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-2">Process Node</label>
          <div className="grid grid-cols-3 gap-2">
            {[3, 5, 7].map((node) => (
              <button
                key={node}
                onClick={() => onConfigChange({ process_node_nm: node })}
                className={`py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  config.process_node_nm === node
                    ? 'bg-nexus-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {node}nm
              </button>
            ))}
          </div>
        </div>

        {/* CPU Cores */}
        <SliderInput
          label="CPU Cores"
          value={config.cpu_cores}
          min={2}
          max={32}
          step={2}
          onChange={(v) => onConfigChange({ cpu_cores: v })}
        />

        {/* GPU Cores */}
        <SliderInput
          label="GPU Cores"
          value={config.gpu_cores}
          min={0}
          max={64}
          step={4}
          onChange={(v) => onConfigChange({ gpu_cores: v })}
        />

        {/* NPU Cores */}
        <SliderInput
          label="NPU Cores"
          value={config.npu_cores}
          min={0}
          max={32}
          step={2}
          onChange={(v) => onConfigChange({ npu_cores: v })}
        />

        {/* L2 Cache */}
        <SliderInput
          label="L2 Cache"
          value={config.l2_cache_mb}
          min={2}
          max={32}
          step={2}
          unit=" MB"
          onChange={(v) => onConfigChange({ l2_cache_mb: v })}
        />

        {/* L3 Cache */}
        <SliderInput
          label="L3 Cache"
          value={config.l3_cache_mb}
          min={0}
          max={128}
          step={8}
          unit=" MB"
          onChange={(v) => onConfigChange({ l3_cache_mb: v })}
        />

        {/* Target Frequency */}
        <SliderInput
          label="Target Frequency"
          value={config.target_frequency_ghz}
          min={1.5}
          max={4.5}
          step={0.1}
          unit=" GHz"
          onChange={(v) => onConfigChange({ target_frequency_ghz: v })}
        />

        {/* PCIe Lanes */}
        <SliderInput
          label="PCIe Lanes"
          value={config.pcie_lanes}
          min={8}
          max={64}
          step={8}
          onChange={(v) => onConfigChange({ pcie_lanes: v })}
        />

        {/* Memory Channels */}
        <SliderInput
          label="Memory Channels"
          value={config.memory_channels}
          min={1}
          max={8}
          step={1}
          onChange={(v) => onConfigChange({ memory_channels: v })}
        />

        {/* Simulate Button */}
        <button
          onClick={onSimulate}
          disabled={isLoading}
          className="w-full py-3 px-4 bg-nexus-600 text-white font-medium rounded-lg hover:bg-nexus-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Simulating...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Run Simulation
            </>
          )}
        </button>
      </div>
    </div>
  );
}
