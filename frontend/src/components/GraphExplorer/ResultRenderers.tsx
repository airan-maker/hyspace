/**
 * Result renderers for each query type.
 * Extracted from GraphExplorer for separation of concerns.
 */
import { LABEL_COLORS, RISK_COLORS } from './constants';

/* ── Shared helpers ──────────────────────────── */

export function RiskBadge({ level }: { level: string }) {
  const color = RISK_COLORS[level] || '#6b7280';
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium text-white"
      style={{ backgroundColor: color }}
    >
      {level}
    </span>
  );
}

export function InfoCell({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <span className="text-xs text-gray-400">{label}</span>
      <p className={`text-sm ${highlight ? 'text-red-400 font-semibold' : 'text-gray-200'}`}>{value}</p>
    </div>
  );
}

function RelatedCard({ color, relation, label, children }: {
  color: string; relation: string; label: string; children: React.ReactNode;
}) {
  return (
    <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
      <div className="flex items-center gap-1.5 mb-1.5">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
        <span className="text-[10px] text-gray-500 font-mono">{relation}</span>
        <span className="text-xs text-gray-400">| {label}</span>
      </div>
      {children}
    </div>
  );
}

/* ── Result renderers ────────────────────────── */

export function AcceleratorContextResult({ data }: { data: Record<string, unknown> }) {
  const acc = data.accelerator as Record<string, unknown> | null;
  const pn = data.process_node as Record<string, unknown> | null;
  const hbm = data.hbm as Record<string, unknown> | null;
  const pkg = data.packaging as Record<string, unknown> | null;
  const models = (data.compatible_models || []) as Record<string, unknown>[];
  const competitors = (data.competitors || []) as string[];

  if (!acc) return <p className="text-gray-400 text-sm">결과가 없습니다.</p>;

  return (
    <div className="space-y-3">
      <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
        <h4 className="text-sm font-semibold text-gray-200 flex items-center gap-2 mb-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: LABEL_COLORS.AIAccelerator }} />
          {String(acc.name || '')}
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {!!acc.vendor && <InfoCell label="제조사" value={String(acc.vendor)} />}
          {!!acc.int8_tops && <InfoCell label="INT8" value={`${String(acc.int8_tops)} TOPS`} />}
          {!!acc.bf16_tflops && <InfoCell label="BF16" value={`${String(acc.bf16_tflops)} TFLOPS`} />}
          {!!acc.tdp_watts && <InfoCell label="TDP" value={`${String(acc.tdp_watts)}W`} />}
          {!!acc.memory_capacity_gb && <InfoCell label="메모리" value={`${String(acc.memory_capacity_gb)}GB`} />}
          {!!acc.msrp_usd && <InfoCell label="MSRP" value={`$${Number(acc.msrp_usd).toLocaleString()}`} />}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {pn && (
          <RelatedCard color={LABEL_COLORS.ProcessNode} relation="MANUFACTURED_ON" label="공정">
            <p className="font-medium text-sm text-gray-200">{String(pn.name || '')}</p>
            {!!pn.node_nm && <p className="text-xs text-gray-400">{String(pn.node_nm)}nm | {String(pn.vendor)}</p>}
          </RelatedCard>
        )}
        {hbm && (
          <RelatedCard color={LABEL_COLORS.HBMGeneration} relation="USES_MEMORY" label="메모리">
            <p className="font-medium text-sm text-gray-200">{String(hbm.generation || hbm.name || '')}</p>
            {!!hbm.bandwidth_per_stack_gbps && <p className="text-xs text-gray-400">{String(hbm.bandwidth_per_stack_gbps)} GB/s</p>}
          </RelatedCard>
        )}
        {pkg && (
          <RelatedCard color={LABEL_COLORS.PackagingTech} relation="USES_PACKAGING" label="패키징">
            <p className="font-medium text-sm text-gray-200">{String(pkg.name || '')}</p>
            {!!pkg.type && <p className="text-xs text-gray-400">Type: {String(pkg.type)}</p>}
          </RelatedCard>
        )}
      </div>

      {!!(models.length > 0 && models[0].model) && (
        <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
          <h4 className="text-xs font-semibold text-gray-400 mb-2">CAN_RUN</h4>
          <div className="flex flex-wrap gap-1.5">
            {models.filter(m => m.model).map((m, i) => (
              <span key={i} className="px-2 py-0.5 text-xs rounded-full border border-pink-800 bg-pink-900/30 text-pink-300">
                {String(m.model)}
              </span>
            ))}
          </div>
        </div>
      )}

      {competitors.length > 0 && competitors[0] && (
        <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
          <h4 className="text-xs font-semibold text-gray-400 mb-2">COMPETES_WITH</h4>
          <div className="flex flex-wrap gap-1.5">
            {competitors.filter(Boolean).map((c, i) => (
              <span key={i} className="px-2 py-0.5 text-xs rounded-full border border-amber-800 bg-amber-900/30 text-amber-300">{c}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function SupplyRiskResult({ data, queryName }: { data: Record<string, unknown>[]; queryName: string }) {
  if (!data || data.length === 0) return <p className="text-gray-400 text-sm">해당 가속기의 공급망 리스크 데이터가 없습니다.</p>;
  const accName = String(data[0]?.accelerator || queryName);

  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-400">
        <strong className="text-gray-200">{accName}</strong>의 공급 리스크 소재
      </p>
      {data.map((item, i) => (
        <div key={i} className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
          <div className="flex items-start justify-between mb-1.5">
            <div>
              <h4 className="text-sm font-semibold text-gray-200">{String(item.material)}</h4>
              <p className="text-xs text-gray-500">{String(item.process_step)} 공정</p>
            </div>
            <div className="flex gap-1">
              {!!item.risk_level && <RiskBadge level={String(item.risk_level)} />}
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            {!!item.geo_concentration && <div><span className="text-gray-500">지역</span><p className="text-gray-300">{String(item.geo_concentration)}</p></div>}
            {!!item.lead_time && <div><span className="text-gray-500">리드타임</span><p className="text-gray-300">{String(item.lead_time)}주</p></div>}
            {!!item.suppliers && <div className="col-span-2"><span className="text-gray-500">공급사</span><p className="text-gray-300">{String(item.suppliers)}</p></div>}
          </div>
        </div>
      ))}
    </div>
  );
}

export function ProcessFlowResult({ data }: { data: Record<string, unknown>[] }) {
  if (!data || data.length === 0) return <p className="text-gray-400 text-sm">공정 플로우 데이터가 없습니다.</p>;
  const moduleColors: Record<string, string> = { FEOL: '#3b82f6', MOL: '#8b5cf6', BEOL: '#06b6d4' };

  return (
    <div className="space-y-1">
      {data.map((step, i) => {
        const mod = String(step.module || '');
        const defects = (step.defects || []) as Record<string, unknown>[];
        const equipment = (step.equipment || []) as string[];
        const materials = (step.materials || []) as Record<string, unknown>[];
        const yieldImpact = String(step.yield_impact || '');

        return (
          <div key={i} className="relative">
            {i < data.length - 1 && (
              <div className="absolute left-[18px] top-[36px] bottom-[-4px] w-px bg-gray-700" />
            )}
            <div className="flex gap-2.5">
              <div
                className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white"
                style={{ backgroundColor: moduleColors[mod] || '#6b7280' }}
              >
                {String(step.step_order || i + 1)}
              </div>
              <div className="flex-1 bg-[#1E2433] border border-gray-700 rounded-lg p-2.5 mb-1">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-200">{String(step.step_name)}</span>
                    <span className="px-1.5 py-0.5 text-[10px] rounded font-medium"
                      style={{ backgroundColor: `${moduleColors[mod] || '#6b7280'}30`, color: moduleColors[mod] || '#6b7280' }}>
                      {mod}
                    </span>
                  </div>
                  {!!yieldImpact && <RiskBadge level={yieldImpact} />}
                </div>
                <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-gray-500">
                  {equipment.length > 0 && !!equipment[0] && (
                    <span>장비: <span className="text-gray-300">{equipment.filter(Boolean).join(', ')}</span></span>
                  )}
                  {!!(materials.length > 0 && materials[0]?.material) && (
                    <span>소재: {materials.filter(m => m.material).map((m, j) => (
                      <span key={j} className="text-gray-300">
                        {String(m.material)}{m.risk ? <span className="text-red-400 ml-0.5">({String(m.risk)})</span> : ''}
                        {j < materials.length - 1 ? ', ' : ''}
                      </span>
                    ))}</span>
                  )}
                  {!!(defects.length > 0 && defects[0]?.defect) && (
                    <span>결함: {defects.filter(d => d.defect).map((d, j) => (
                      <span key={j} className="text-orange-400">
                        {String(d.defect)}{d.kill_ratio ? ` (${String(d.kill_ratio)}%)` : ''}
                        {j < defects.length - 1 ? ', ' : ''}
                      </span>
                    ))}</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function EquipmentImpactResult({ data }: { data: Record<string, unknown> }) {
  if (!data || !data.equipment) return <p className="text-gray-400 text-sm">장비 정보가 없습니다.</p>;

  const failureModes = (data.failure_modes || []) as Record<string, unknown>[];
  const affectedSteps = (data.affected_steps || []) as string[];
  const defects = (data.potential_defects || []) as Record<string, unknown>[];

  return (
    <div className="space-y-3">
      <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
        <h4 className="text-sm font-semibold text-gray-200 mb-2">{String(data.equipment)}</h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {!!data.vendor && <InfoCell label="제조사" value={String(data.vendor)} />}
          {!!data.category && <InfoCell label="카테고리" value={String(data.category)} />}
          {!!data.mtbf && <InfoCell label="MTBF" value={`${String(data.mtbf)}h`} />}
          {!!data.price_m && <InfoCell label="가격" value={`$${String(data.price_m)}M`} />}
        </div>
      </div>
      {!!(failureModes.length > 0 && failureModes[0]?.mode) && (
        <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
          <h4 className="text-xs font-semibold text-gray-400 mb-2">고장 모드</h4>
          <div className="space-y-1.5">
            {failureModes.filter(f => f.mode).map((fm, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-gray-300">{String(fm.mode)}</span>
                <div className="flex gap-3 text-xs text-gray-500">
                  {!!fm.mtbf && <span>MTBF: {String(fm.mtbf)}h</span>}
                  {!!fm.mttr && <span>MTTR: {String(fm.mttr)}h</span>}
                  {!!fm.wafer_risk && <span className="text-red-400">위험: {String(fm.wafer_risk)}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="grid grid-cols-2 gap-2">
        {affectedSteps.length > 0 && !!affectedSteps[0] && (
          <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-gray-400 mb-1.5">영향 공정 ({affectedSteps.filter(Boolean).length})</h4>
            <div className="flex flex-wrap gap-1">
              {affectedSteps.filter(Boolean).map((s, i) => (
                <span key={i} className="px-2 py-0.5 text-xs rounded bg-indigo-900/40 text-indigo-300">{s}</span>
              ))}
            </div>
          </div>
        )}
        {!!(defects.length > 0 && defects[0]?.defect) && (
          <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-gray-400 mb-1.5">발생 가능 결함</h4>
            <div className="flex flex-wrap gap-1">
              {defects.filter(d => d.defect).map((d, i) => (
                <span key={i} className="px-2 py-0.5 text-xs rounded bg-orange-900/40 text-orange-300">
                  {String(d.defect)} {d.severity ? `(${String(d.severity)})` : ''}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function MaterialDependencyResult({ data }: { data: Record<string, unknown> }) {
  if (!data || !data.material) return <p className="text-gray-400 text-sm">소재 정보가 없습니다.</p>;

  const steps = (data.dependent_steps || []) as Record<string, unknown>[];
  const equipment = (data.related_equipment || []) as string[];

  return (
    <div className="space-y-3">
      <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {!!data.supply_risk && <InfoCell label="공급 리스크" value={String(data.supply_risk)} highlight />}
          {!!data.criticality && <InfoCell label="중요도" value={String(data.criticality)} />}
          {!!data.geo && <InfoCell label="지역 집중" value={String(data.geo)} />}
          {!!data.lead_time && <InfoCell label="리드타임" value={`${String(data.lead_time)}주`} />}
          {!!data.suppliers && <InfoCell label="공급사" value={String(data.suppliers)} />}
        </div>
      </div>
      {!!(steps.length > 0 && steps[0]?.step) && (
        <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
          <h4 className="text-xs font-semibold text-gray-400 mb-2">의존 공정 ({steps.filter(s => s.step).length})</h4>
          <div className="space-y-1">
            {steps.filter(s => s.step).map((s, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-gray-300">{String(s.step)}</span>
                <div className="flex gap-2">
                  {!!s.module && <span className="text-xs text-gray-500">{String(s.module)}</span>}
                  {!!s.yield_impact && <RiskBadge level={String(s.yield_impact)} />}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {equipment.length > 0 && !!equipment[0] && (
        <div className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
          <h4 className="text-xs font-semibold text-gray-400 mb-1.5">관련 장비</h4>
          <div className="flex flex-wrap gap-1">
            {equipment.filter(Boolean).map((eq, i) => (
              <span key={i} className="px-2 py-0.5 text-xs rounded bg-green-900/40 text-green-300">{eq}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function CriticalMaterialsResult({ data }: { data: Record<string, unknown>[] }) {
  if (!data || data.length === 0) return <p className="text-gray-400 text-sm">핵심 소재 리스크 데이터가 없습니다.</p>;

  return (
    <div className="overflow-hidden rounded-lg border border-gray-700">
      <table className="w-full text-sm">
        <thead className="bg-[#111420]">
          <tr>
            <th className="text-left px-3 py-2 text-xs font-medium text-gray-400">소재</th>
            <th className="text-center px-3 py-2 text-xs font-medium text-gray-400">리스크</th>
            <th className="text-center px-3 py-2 text-xs font-medium text-gray-400">영향 공정</th>
            <th className="text-left px-3 py-2 text-xs font-medium text-gray-400">지역</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {data.map((mat, i) => (
            <tr key={i} className="hover:bg-gray-800/50">
              <td className="px-3 py-2 font-medium text-gray-200">{String(mat.material)}</td>
              <td className="px-3 py-2 text-center">{!!mat.risk_level && <RiskBadge level={String(mat.risk_level)} />}</td>
              <td className="px-3 py-2 text-center font-mono text-gray-400">{String(mat.affected_step_count || 0)}</td>
              <td className="px-3 py-2 text-gray-400 text-xs">{String(mat.geo || '-')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PathResult({ data }: { data: Record<string, unknown>[] }) {
  if (!data || data.length === 0) return <p className="text-gray-400 text-sm">경로를 찾을 수 없습니다.</p>;

  return (
    <div className="space-y-2">
      {data.map((path, pi) => {
        const nodes = (path.path_nodes || []) as { label: string; name: string }[];
        const rels = (path.path_relationships || []) as string[];
        return (
          <div key={pi} className="bg-[#1E2433] border border-gray-700 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-1.5">{String(path.hops || '?')} hops</div>
            <div className="flex items-center flex-wrap gap-1">
              {nodes.map((node, ni) => (
                <div key={ni} className="flex items-center gap-1">
                  <span
                    className="px-2 py-0.5 text-xs rounded-full font-medium text-white"
                    style={{ backgroundColor: LABEL_COLORS[node.label] || '#6b7280' }}
                  >
                    {node.name}
                  </span>
                  {ni < rels.length && (
                    <span className="text-[10px] text-gray-500 font-mono px-1">{rels[ni]}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ── Result Panel Router ─────────────────────── */

export function ResultPanel({ result, selectedQuery, isLoading, error }: {
  result: unknown;
  selectedQuery: string;
  isLoading: boolean;
  error: string | null;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin w-6 h-6 border-2 border-gray-600 border-t-blue-400 rounded-full" />
        <span className="ml-3 text-gray-400 text-sm">쿼리 실행 중...</span>
      </div>
    );
  }

  if (error) {
    return <p className="text-red-400 text-sm p-2">{error}</p>;
  }

  if (!result || !selectedQuery) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 text-sm">탐색 카드를 클릭하거나 검색하여 질의하세요</p>
      </div>
    );
  }

  switch (selectedQuery) {
    case 'h100_context':
    case 'accelerator_context':
      return <AcceleratorContextResult data={result as Record<string, unknown>} />;
    case 'h100_supply_risks':
    case 'b200_supply_risks':
    case 'accelerator_risk':
      return <SupplyRiskResult data={result as Record<string, unknown>[]} queryName={selectedQuery} />;
    case 'process_flow':
      return <ProcessFlowResult data={result as Record<string, unknown>[]} />;
    case 'euv_impact':
    case 'equipment_impact':
      return <EquipmentImpactResult data={result as Record<string, unknown>} />;
    case 'euv_resist_dep':
    case 'material_dependency':
      return <MaterialDependencyResult data={result as Record<string, unknown>} />;
    case 'critical_materials':
      return <CriticalMaterialsResult data={result as Record<string, unknown>[]} />;
    case 'h100_to_euv':
    case 'entity_path':
      return <PathResult data={result as Record<string, unknown>[]} />;
    default:
      return (
        <div className="bg-[#111420] rounded-lg p-3 overflow-auto max-h-[400px]">
          <pre className="text-xs font-mono text-gray-300 whitespace-pre-wrap">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      );
  }
}
