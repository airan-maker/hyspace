import type {
  WorkloadProfile,
  WorkloadPresetSummary,
  ComputeRequirements,
  MemoryRequirements,
  PowerConstraints,
  DeploymentContext,
  WorkloadType,
  FormFactor,
  CoolingType,
  Precision,
} from '../../types/workload';

interface WorkloadInputPanelProps {
  profile: WorkloadProfile;
  presets: WorkloadPresetSummary[];
  selectedPresetId: string | null;
  onProfileChange: (updates: Partial<WorkloadProfile>) => void;
  onComputeChange: (updates: Partial<ComputeRequirements>) => void;
  onMemoryChange: (updates: Partial<MemoryRequirements>) => void;
  onPowerChange: (updates: Partial<PowerConstraints>) => void;
  onDeploymentChange: (updates: Partial<DeploymentContext>) => void;
  onPresetSelect: (presetId: string) => void;
  onAnalyze: () => void;
  isLoading: boolean;
  isPresetsLoading: boolean;
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
        <label className="text-sm font-medium text-gray-300">{label}</label>
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

interface SelectInputProps {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}

function SelectInput({ label, value, options, onChange }: SelectInputProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-300 block">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-600 bg-[#111420] rounded-lg text-sm focus:ring-2 focus:ring-nexus-500 focus:border-nexus-500"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

const WORKLOAD_TYPES: { value: WorkloadType; label: string }[] = [
  { value: 'AI_INFERENCE', label: 'AI Inference' },
  { value: 'AI_TRAINING', label: 'AI Training' },
  { value: 'IMAGE_PROCESSING', label: 'Image Processing' },
  { value: 'VIDEO_ENCODING', label: 'Video Encoding' },
  { value: 'SCIENTIFIC_COMPUTE', label: 'Scientific Compute' },
  { value: 'DATABASE', label: 'Database' },
  { value: 'NETWORKING', label: 'Networking' },
  { value: 'GENERAL_PURPOSE', label: 'General Purpose' },
];

const PRECISION_OPTIONS: { value: Precision; label: string }[] = [
  { value: 'INT4', label: 'INT4' },
  { value: 'INT8', label: 'INT8' },
  { value: 'FP16', label: 'FP16' },
  { value: 'BF16', label: 'BF16' },
  { value: 'FP32', label: 'FP32' },
];

const FORM_FACTOR_OPTIONS: { value: FormFactor; label: string }[] = [
  { value: 'DATA_CENTER', label: 'Data Center' },
  { value: 'EDGE_SERVER', label: 'Edge Server' },
  { value: 'EMBEDDED', label: 'Embedded' },
  { value: 'MOBILE', label: 'Mobile' },
];

const COOLING_OPTIONS: { value: CoolingType; label: string }[] = [
  { value: 'AIR', label: 'Air Cooling' },
  { value: 'LIQUID', label: 'Liquid Cooling' },
  { value: 'PASSIVE', label: 'Passive' },
];

export function WorkloadInputPanel({
  profile,
  presets,
  selectedPresetId,
  onProfileChange,
  onComputeChange,
  onMemoryChange,
  onPowerChange,
  onDeploymentChange,
  onPresetSelect,
  onAnalyze,
  isLoading,
  isPresetsLoading,
}: WorkloadInputPanelProps) {
  return (
    <div className="card">
      <h2 className="card-header flex items-center gap-2">
        <svg className="w-5 h-5 text-nexus-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
        Workload Profile
      </h2>

      <div className="space-y-6">
        {/* Preset Selection */}
        <div>
          <label className="text-sm font-medium text-gray-300 block mb-2">Load Preset</label>
          <div className="flex flex-wrap gap-2">
            {isPresetsLoading ? (
              <div className="animate-pulse flex gap-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-8 w-24 bg-gray-700 rounded-lg" />
                ))}
              </div>
            ) : (
              presets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => onPresetSelect(preset.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    selectedPresetId === preset.id
                      ? 'bg-nexus-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                  title={preset.description}
                >
                  {preset.name}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Workload Name & Type */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300 block">Name</label>
            <input
              type="text"
              value={profile.name}
              onChange={(e) => onProfileChange({ name: e.target.value })}
              placeholder="My Workload"
              className="w-full px-3 py-2 border border-gray-600 bg-[#111420] rounded-lg text-sm focus:ring-2 focus:ring-nexus-500 focus:border-nexus-500"
            />
          </div>
          <SelectInput
            label="Workload Type"
            value={profile.workload_type}
            options={WORKLOAD_TYPES}
            onChange={(v) => onProfileChange({ workload_type: v as WorkloadType })}
          />
        </div>

        {/* Compute Requirements Section */}
        <div className="border-t pt-4">
          <h3 className="text-sm font-semibold text-gray-200 mb-4 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
            Compute Requirements
          </h3>

          <div className="space-y-4">
            <SliderInput
              label="Operations per Inference"
              value={profile.compute_requirements.operations_per_inference}
              min={1}
              max={500}
              step={1}
              unit=" TOPS"
              onChange={(v) => onComputeChange({ operations_per_inference: v })}
            />

            <SliderInput
              label="Target Latency"
              value={profile.compute_requirements.target_latency_ms}
              min={1}
              max={1000}
              step={1}
              unit=" ms"
              onChange={(v) => onComputeChange({ target_latency_ms: v })}
            />

            <div className="grid grid-cols-2 gap-4">
              <SliderInput
                label="Batch Size"
                value={profile.compute_requirements.batch_size}
                min={1}
                max={64}
                step={1}
                onChange={(v) => onComputeChange({ batch_size: v })}
              />
              <SelectInput
                label="Precision"
                value={profile.compute_requirements.precision}
                options={PRECISION_OPTIONS}
                onChange={(v) => onComputeChange({ precision: v as Precision })}
              />
            </div>
          </div>
        </div>

        {/* Memory Requirements Section */}
        <div className="border-t pt-4">
          <h3 className="text-sm font-semibold text-gray-200 mb-4 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Memory Requirements
          </h3>

          <div className="space-y-4">
            <SliderInput
              label="Model Size"
              value={profile.memory_requirements.model_size_gb}
              min={0.1}
              max={200}
              step={0.1}
              unit=" GB"
              onChange={(v) => onMemoryChange({ model_size_gb: v })}
            />

            <SliderInput
              label="Activation Memory"
              value={profile.memory_requirements.activation_memory_gb}
              min={0}
              max={50}
              step={0.5}
              unit=" GB"
              onChange={(v) => onMemoryChange({ activation_memory_gb: v })}
            />

            <SliderInput
              label="KV Cache (LLM)"
              value={profile.memory_requirements.kv_cache_gb}
              min={0}
              max={100}
              step={1}
              unit=" GB"
              onChange={(v) => onMemoryChange({ kv_cache_gb: v })}
            />

            <SliderInput
              label="Bandwidth Requirement"
              value={profile.memory_requirements.bandwidth_requirement_gbps}
              min={50}
              max={5000}
              step={50}
              unit=" GB/s"
              onChange={(v) => onMemoryChange({ bandwidth_requirement_gbps: v })}
            />
          </div>
        </div>

        {/* Power Constraints Section */}
        <div className="border-t pt-4">
          <h3 className="text-sm font-semibold text-gray-200 mb-4 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Power Constraints
          </h3>

          <div className="space-y-4">
            <SliderInput
              label="Max TDP"
              value={profile.power_constraints.max_tdp_watts}
              min={10}
              max={800}
              step={10}
              unit=" W"
              onChange={(v) => onPowerChange({ max_tdp_watts: v })}
            />

            <SliderInput
              label="Target Efficiency"
              value={profile.power_constraints.target_efficiency_tops_per_watt}
              min={0.1}
              max={20}
              step={0.1}
              unit=" TOPS/W"
              onChange={(v) => onPowerChange({ target_efficiency_tops_per_watt: v })}
            />
          </div>
        </div>

        {/* Deployment Context Section */}
        <div className="border-t pt-4">
          <h3 className="text-sm font-semibold text-gray-200 mb-4 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            Deployment Context
          </h3>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <SelectInput
                label="Form Factor"
                value={profile.deployment_context.form_factor}
                options={FORM_FACTOR_OPTIONS}
                onChange={(v) => onDeploymentChange({ form_factor: v as FormFactor })}
              />
              <SelectInput
                label="Cooling"
                value={profile.deployment_context.cooling}
                options={COOLING_OPTIONS}
                onChange={(v) => onDeploymentChange({ cooling: v as CoolingType })}
              />
            </div>

            <SliderInput
              label="Volume per Year"
              value={profile.deployment_context.volume_per_year}
              min={100}
              max={1000000}
              step={100}
              onChange={(v) => onDeploymentChange({ volume_per_year: v })}
            />
          </div>
        </div>

        {/* Analyze Button */}
        <button
          onClick={onAnalyze}
          disabled={isLoading}
          className="w-full py-3 px-4 bg-nexus-600 text-white font-medium rounded-lg hover:bg-nexus-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Analyzing...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              Analyze Workload
            </>
          )}
        </button>
      </div>
    </div>
  );
}
