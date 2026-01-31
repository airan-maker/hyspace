import { useState, useEffect } from 'react';
import {
  getSeedScenarios,
  previewSeedData,
  applySeedData,
  getSeedStatus,
  clearSeedData,
  type SeedScenario,
  type SeedPreview,
  type SeedApplyResult,
  type SeedStatus,
} from '../../services/api';

type WizardStep = 'select' | 'preview' | 'apply' | 'done';

const TAG_COLORS: Record<string, string> = {
  EUV: 'bg-purple-100 text-purple-700',
  AI: 'bg-blue-100 text-blue-700',
  HBM3: 'bg-cyan-100 text-cyan-700',
  HBM3E: 'bg-cyan-100 text-cyan-700',
  CoWoS: 'bg-indigo-100 text-indigo-700',
  DUV: 'bg-amber-100 text-amber-700',
  GAA: 'bg-green-100 text-green-700',
  'Ramp-up': 'bg-orange-100 text-orange-700',
  RibbonFET: 'bg-emerald-100 text-emerald-700',
  PowerVia: 'bg-teal-100 text-teal-700',
  'R&D': 'bg-rose-100 text-rose-700',
};

export default function SeedDataWizard() {
  const [step, setStep] = useState<WizardStep>('select');
  const [scenarios, setScenarios] = useState<SeedScenario[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [preview, setPreview] = useState<SeedPreview | null>(null);
  const [result, setResult] = useState<SeedApplyResult | null>(null);
  const [dbStatus, setDbStatus] = useState<SeedStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clearExisting, setClearExisting] = useState(false);

  // Load scenarios on mount
  useEffect(() => {
    loadScenarios();
    loadStatus();
  }, []);

  async function loadScenarios() {
    try {
      const data = await getSeedScenarios();
      setScenarios(data.scenarios);
    } catch (e) {
      setError('Failed to load scenarios. Is the backend running?');
    }
  }

  async function loadStatus() {
    try {
      const status = await getSeedStatus();
      setDbStatus(status);
    } catch {
      // DB not available yet - OK
    }
  }

  async function handlePreview() {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await previewSeedData(selectedId);
      setPreview(data);
      setStep('preview');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Preview failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleApply() {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await applySeedData(selectedId, clearExisting);
      setResult(data);
      setStep('done');
      loadStatus();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Apply failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleClear() {
    if (!confirm('Are you sure? This will delete ALL seed data from the database.')) return;
    setLoading(true);
    try {
      await clearSeedData();
      loadStatus();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Clear failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  const totalRecords = dbStatus
    ? Object.values(dbStatus).reduce((a, b) => a + b, 0)
    : 0;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Seed Data Agent</h1>
        <p className="text-gray-500 mt-1">
          Select a scenario to auto-generate realistic seed data powered by semiconductor domain ontology.
        </p>
      </div>

      {/* DB Status Banner */}
      {dbStatus && (
        <div className={`mb-6 rounded-lg border p-4 ${totalRecords > 0 ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
          <div className="flex items-center justify-between">
            <div>
              <span className={`text-sm font-medium ${totalRecords > 0 ? 'text-green-800' : 'text-gray-600'}`}>
                Database Status: {totalRecords > 0 ? `${totalRecords} records loaded` : 'Empty - select a scenario to get started'}
              </span>
              {totalRecords > 0 && (
                <div className="flex gap-3 mt-1 text-xs text-green-600">
                  {Object.entries(dbStatus).map(([key, count]) => (
                    count > 0 && <span key={key}>{key.replace(/_/g, ' ')}: {count}</span>
                  ))}
                </div>
              )}
            </div>
            {totalRecords > 0 && (
              <button
                onClick={handleClear}
                disabled={loading}
                className="text-xs text-red-600 hover:text-red-800 border border-red-200 rounded px-2 py-1"
              >
                Clear All
              </button>
            )}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm">
          {error}
          <button onClick={() => setError(null)} className="ml-2 text-red-500 underline">dismiss</button>
        </div>
      )}

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-6">
        {(['select', 'preview', 'apply', 'done'] as WizardStep[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step === s ? 'bg-nexus-600 text-white' :
              (['select', 'preview', 'apply', 'done'].indexOf(step) > i) ? 'bg-nexus-100 text-nexus-700' :
              'bg-gray-100 text-gray-400'
            }`}>
              {i + 1}
            </div>
            {i < 3 && <div className="w-8 h-px bg-gray-300" />}
          </div>
        ))}
        <span className="ml-2 text-sm text-gray-500">
          {step === 'select' && 'Select Scenario'}
          {step === 'preview' && 'Preview Data'}
          {step === 'apply' && 'Applying...'}
          {step === 'done' && 'Complete'}
        </span>
      </div>

      {/* Step 1: Select */}
      {step === 'select' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {scenarios.map((s) => (
            <ScenarioCard
              key={s.scenario_id}
              scenario={s}
              selected={selectedId === s.scenario_id}
              onSelect={() => setSelectedId(s.scenario_id)}
            />
          ))}

          {selectedId && (
            <div className="col-span-full mt-4 flex items-center gap-4">
              <button
                onClick={handlePreview}
                disabled={loading}
                className="px-6 py-2.5 bg-nexus-600 text-white rounded-lg hover:bg-nexus-700 disabled:opacity-50 font-medium"
              >
                {loading ? 'Generating preview...' : 'Preview Seed Data'}
              </button>
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={clearExisting}
                  onChange={(e) => setClearExisting(e.target.checked)}
                  className="rounded"
                />
                Clear existing data before loading
              </label>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Preview */}
      {step === 'preview' && preview && (
        <div>
          <PreviewPanel preview={preview} />

          <div className="mt-6 flex gap-3">
            <button
              onClick={() => setStep('select')}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={handleApply}
              disabled={loading}
              className="px-6 py-2.5 bg-nexus-600 text-white rounded-lg hover:bg-nexus-700 disabled:opacity-50 font-medium"
            >
              {loading ? 'Applying to database...' : 'Apply to Database'}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Done */}
      {step === 'done' && result && (
        <div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-green-800">{result.message}</h3>
                <p className="text-sm text-green-600">Scenario: {result.scenario.name}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(result.loaded).map(([key, val]) => {
                if (key === 'cleared') return null;
                const v = val as { created: number; skipped: number };
                return (
                  <div key={key} className="bg-white rounded-lg p-3 border border-green-100">
                    <div className="text-xs text-gray-500">{key.replace(/_/g, ' ')}</div>
                    <div className="text-lg font-semibold text-green-700">{v.created}</div>
                    {v.skipped > 0 && <div className="text-xs text-gray-400">{v.skipped} skipped</div>}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              onClick={() => { setStep('select'); setResult(null); setPreview(null); }}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Load Another Scenario
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


// ============================================================
// Sub-components
// ============================================================

function ScenarioCard({
  scenario: s,
  selected,
  onSelect,
}: {
  scenario: SeedScenario;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={`text-left p-5 rounded-xl border-2 transition-all ${
        selected
          ? 'border-nexus-500 bg-nexus-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-gray-900">{s.name_kr}</h3>
        {selected && (
          <div className="w-5 h-5 bg-nexus-600 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}
      </div>
      <p className="text-xs text-gray-500 mb-3">{s.name}</p>
      <p className="text-sm text-gray-600 mb-3 line-clamp-3">{s.description}</p>

      <div className="flex flex-wrap gap-1 mb-3">
        {s.tags.map((tag) => (
          <span
            key={tag}
            className={`px-2 py-0.5 text-xs rounded-full font-medium ${TAG_COLORS[tag] || 'bg-gray-100 text-gray-600'}`}
          >
            {tag}
          </span>
        ))}
      </div>

      <div className="text-xs text-gray-400 space-y-0.5">
        <div>Process: <span className="text-gray-600 font-medium">{s.process_node}</span></div>
        {s.wspm && <div>WSPM: <span className="text-gray-600">{s.wspm?.toLocaleString()}</span></div>}
        {s.equipment_count && <div>Equipment: <span className="text-gray-600">{s.equipment_count} units</span></div>}
      </div>
    </button>
  );
}


function PreviewPanel({ preview }: { preview: SeedPreview }) {
  const categories = [
    'process_nodes', 'ip_blocks', 'fab_equipment', 'wip_items',
    'materials', 'suppliers', 'wafer_records', 'yield_events',
  ];

  const LABELS: Record<string, string> = {
    process_nodes: 'Process Nodes',
    ip_blocks: 'IP Blocks',
    fab_equipment: 'Fab Equipment',
    wip_items: 'WIP Items',
    materials: 'Materials',
    suppliers: 'Suppliers',
    wafer_records: 'Wafer Records',
    yield_events: 'Yield Events',
  };

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h3 className="font-semibold text-gray-900 mb-3">Preview Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {categories.map((cat) => {
            const data = preview[cat] as { total_count: number } | undefined;
            return (
              <div key={cat} className="bg-gray-50 rounded-lg p-3">
                <div className="text-xs text-gray-500">{LABELS[cat]}</div>
                <div className="text-xl font-bold text-gray-900">{data?.total_count ?? 0}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Ontology Sources */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h3 className="font-semibold text-gray-900 mb-3">Ontology Sources</h3>
        <div className="space-y-1">
          {preview.summary.ontology_sources.map((src, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-gray-600">
              <svg className="w-4 h-4 text-nexus-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {src}
            </div>
          ))}
        </div>
      </div>

      {/* Sample Data Accordion */}
      {categories.map((cat) => {
        const data = preview[cat] as { total_count: number; sample: Record<string, unknown>[] } | undefined;
        if (!data || data.total_count === 0) return null;
        return (
          <SampleAccordion
            key={cat}
            label={LABELS[cat]}
            count={data.total_count}
            samples={data.sample}
          />
        );
      })}
    </div>
  );
}


function SampleAccordion({
  label,
  count,
  samples,
}: {
  label: string;
  count: number;
  samples: Record<string, unknown>[];
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50"
      >
        <span className="font-medium text-gray-900">{label} ({count})</span>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="text-xs text-gray-500 mb-2">Showing first {samples.length} of {count} items</div>
          <pre className="text-xs text-gray-700 overflow-x-auto max-h-64 overflow-y-auto bg-white rounded p-3 border">
            {JSON.stringify(samples, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
