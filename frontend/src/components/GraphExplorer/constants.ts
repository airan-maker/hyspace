/** 노드 라벨 → 컬러 매핑 */
export const LABEL_COLORS: Record<string, string> = {
  AIAccelerator: '#f59e0b',
  ProcessNode: '#3b82f6',
  HBMGeneration: '#8b5cf6',
  PackagingTech: '#06b6d4',
  AIModel: '#ec4899',
  Material: '#ef4444',
  Equipment: '#10b981',
  ProcessStep: '#6366f1',
  DefectType: '#f97316',
  EquipmentFailure: '#dc2626',
};

/** 관계 타입 → 엣지 스타일 */
export const RELATIONSHIP_STYLES: Record<string, { color: string; dashed?: boolean }> = {
  MANUFACTURED_ON: { color: '#3b82f6' },
  USES_MEMORY: { color: '#8b5cf6' },
  USES_PACKAGING: { color: '#06b6d4' },
  CAN_RUN: { color: '#ec4899' },
  COMPETES_WITH: { color: '#f59e0b', dashed: true },
  REQUIRES_MATERIAL: { color: '#ef4444' },
  REQUIRES_EQUIPMENT: { color: '#10b981' },
  CAUSES_DEFECT: { color: '#f97316' },
  NEXT_STEP: { color: '#6366f1' },
  FAILURE_OF: { color: '#dc2626', dashed: true },
  SUCCESSOR_OF: { color: '#3b82f6', dashed: true },
};

/** 리스크 레벨 → 컬러 */
export const RISK_COLORS: Record<string, string> = {
  VERY_HIGH: '#dc2626',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#22c55e',
  CRITICAL: '#dc2626',
  CATASTROPHIC: '#7f1d1d',
  MAJOR: '#b91c1c',
  MINOR: '#ca8a04',
};

/** 공정 모듈 → 컬러 */
export const MODULE_COLORS: Record<string, string> = {
  FEOL: '#3b82f6',
  MOL: '#8b5cf6',
  BEOL: '#06b6d4',
};

/** 프리셋 쿼리 → 포컬 노드 키워드 매핑 (서브그래프 추출용) */
export const PRESET_FOCAL_NODES: Record<string, string[]> = {
  h100_context: ['H100'],
  h100_supply_risks: ['H100'],
  b200_supply_risks: ['B200'],
  euv_impact: ['ASML', 'NXE'],
  euv_resist_dep: ['EUV Photoresist'],
  critical_materials: [],
  h100_to_euv: ['H100', 'EUV Photoresist'],
  process_flow: [],
};

/** 추천 탐색 카드 정의 (QueryHub 탐색 탭) */
export interface SuggestedQuery {
  presetId: string;
  title: string;
  desc: string;
}

export interface ExplorationCategory {
  category: string;
  icon: 'shield' | 'cog' | 'link';
  color: string;
  queries: SuggestedQuery[];
}

export const SUGGESTED_EXPLORATIONS: ExplorationCategory[] = [
  {
    category: '공급망 리스크',
    icon: 'shield',
    color: '#ef4444',
    queries: [
      { presetId: 'h100_supply_risks', title: 'H100 공급 리스크', desc: 'H100 제조에 필요한 소재 중 공급 위험이 높은 항목' },
      { presetId: 'b200_supply_risks', title: 'B200 공급 리스크', desc: 'B200 Blackwell 아키텍처의 공급망 리스크' },
      { presetId: 'critical_materials', title: '핵심 소재 리스크', desc: 'HIGH 이상 공급 리스크를 가진 전체 소재 목록' },
    ],
  },
  {
    category: '제조 공정',
    icon: 'cog',
    color: '#6366f1',
    queries: [
      { presetId: 'process_flow', title: '전체 공정 플로우', desc: 'FEOL→MOL→BEOL 13단계 + 결함/장비/소재' },
      { presetId: 'euv_impact', title: 'EUV 장비 영향', desc: 'ASML EUV 장비 고장 시 전체 영향 분석' },
    ],
  },
  {
    category: '관계 탐색',
    icon: 'link',
    color: '#3b82f6',
    queries: [
      { presetId: 'h100_context', title: 'H100 컨텍스트', desc: '공정·메모리·패키징·호환 모델 (1-hop)' },
      { presetId: 'euv_resist_dep', title: 'EUV 소재 의존성', desc: 'EUV 레지스트 공급 중단 시 영향 체인' },
      { presetId: 'h100_to_euv', title: 'H100 ↔ EUV 경로', desc: '가속기에서 소재까지 관계 경로 탐색' },
    ],
  },
];

/** 질의 템플릿 정의 (QueryHub 템플릿 탭) */
export interface TemplateParam {
  key: string;
  label: string;
  optionSource: string;
}

export interface QueryTemplate {
  id: string;
  title: string;
  desc: string;
  params: TemplateParam[];
  resultQueryMap: string;
}

export const QUERY_TEMPLATES: QueryTemplate[] = [
  {
    id: 'accelerator_risk',
    title: '가속기 공급 리스크 분석',
    desc: '선택한 가속기의 제조에 필요한 소재 중 공급 리스크가 높은 항목을 분석합니다',
    params: [{ key: 'accelerator', label: '가속기', optionSource: 'accelerators' }],
    resultQueryMap: 'supply_risks',
  },
  {
    id: 'accelerator_context',
    title: '가속기 전체 컨텍스트',
    desc: '선택한 가속기의 공정, 메모리, 패키징, AI 모델을 한눈에 확인',
    params: [{ key: 'accelerator', label: '가속기', optionSource: 'accelerators' }],
    resultQueryMap: 'context',
  },
  {
    id: 'equipment_impact',
    title: '장비 고장 영향 분석',
    desc: '장비 벤더 선택 → 해당 장비 고장 시 영향받는 공정/결함/소재',
    params: [{ key: 'vendor', label: '장비 벤더', optionSource: 'equipment_vendors' }],
    resultQueryMap: 'equipment',
  },
  {
    id: 'material_dependency',
    title: '소재 의존성 체인',
    desc: '특정 소재 공급 중단 시 영향받는 공정과 장비',
    params: [{ key: 'material', label: '소재', optionSource: 'materials' }],
    resultQueryMap: 'material',
  },
  {
    id: 'entity_path',
    title: '엔티티 간 경로 탐색',
    desc: '두 엔티티 사이의 최단 경로(관계 흐름)를 탐색합니다',
    params: [
      { key: 'from', label: '시작 노드', optionSource: 'all_nodes' },
      { key: 'to', label: '끝 노드', optionSource: 'all_nodes' },
    ],
    resultQueryMap: 'path',
  },
];
