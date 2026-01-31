"""
Ontology API

도메인 지식 조회 및 시드 데이터 생성 에이전트 API
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.ontology import (
    SemiconductorOntology,
    AIIndustryOntology,
    MaterialsKnowledgeBase,
    EquipmentKnowledgeBase,
    ProcessFlowOntology,
    FailureModeOntology,
)

router = APIRouter(prefix="/ontology", tags=["Domain Ontology"])


# ============================================================
# Semiconductor
# ============================================================

@router.get("/semiconductor/nodes")
def list_process_nodes(vendor: Optional[str] = None):
    """공정 노드 목록"""
    if vendor:
        from app.ontology.semiconductor import FoundryVendor
        try:
            v = FoundryVendor(vendor)
            nodes = SemiconductorOntology.get_nodes_by_vendor(v)
        except ValueError:
            raise HTTPException(400, f"Unknown vendor: {vendor}. Use TSMC, Samsung Foundry, Intel Foundry")
    else:
        nodes = SemiconductorOntology.get_all_nodes()

    return {
        "count": len(nodes),
        "nodes": {
            k: {
                "name": v.name,
                "node_nm": v.node_nm,
                "vendor": v.vendor.value,
                "transistor_type": v.transistor_type,
                "logic_density_mtr_per_mm2": v.logic_density_mtr_per_mm2,
                "euv_layers": v.euv_layers,
                "wafer_cost_usd": v.wafer_cost_usd,
                "typical_yield_pct": v.typical_yield_pct,
                "volume_production_year": v.volume_production_year,
                "description": v.description,
            }
            for k, v in nodes.items()
        }
    }


@router.get("/semiconductor/nodes/{node_name}")
def get_process_node(node_name: str):
    """공정 노드 상세 사양"""
    node = SemiconductorOntology.get_node(node_name)
    if not node:
        raise HTTPException(404, f"Node not found: {node_name}")
    return node


@router.get("/semiconductor/packaging")
def list_packaging():
    """패키징 기술 목록"""
    pkgs = SemiconductorOntology.get_all_packaging()
    return {k: {"name": v.name, "vendor": v.vendor,
                "max_hbm_stacks": v.max_hbm_stacks,
                "typical_applications": v.typical_applications,
                "description": v.description}
            for k, v in pkgs.items()}


@router.get("/semiconductor/die-calculator")
def calculate_die_count(
    die_width_mm: float = Query(..., description="Die width (mm)"),
    die_height_mm: float = Query(..., description="Die height (mm)"),
    wafer_diameter_mm: int = Query(default=300),
):
    """웨이퍼당 다이 수 계산"""
    gross = SemiconductorOntology.calculate_gross_die_per_wafer(
        die_width_mm, die_height_mm, wafer_diameter_mm
    )
    return {
        "die_width_mm": die_width_mm,
        "die_height_mm": die_height_mm,
        "die_area_mm2": round(die_width_mm * die_height_mm, 2),
        "wafer_diameter_mm": wafer_diameter_mm,
        "gross_die_per_wafer": gross,
    }


@router.get("/semiconductor/oee-standards")
def get_oee_standards():
    """OEE 표준 (SEMI E10)"""
    return SemiconductorOntology.get_oee_standards()


# ============================================================
# AI Industry
# ============================================================

@router.get("/ai/accelerators")
def list_accelerators(vendor: Optional[str] = None):
    """AI 가속기 목록"""
    if vendor:
        from app.ontology.ai_industry import AcceleratorVendor
        try:
            v = AcceleratorVendor(vendor)
            accs = AIIndustryOntology.get_accelerators_by_vendor(v)
        except ValueError:
            raise HTTPException(400, f"Unknown vendor: {vendor}")
        return {"count": len(accs), "accelerators": [
            {"name": a.name, "process_node": a.process_node,
             "bf16_tflops": a.compute.bf16_tflops,
             "memory_gb": a.memory.capacity_gb, "memory_type": a.memory.type,
             "tdp_watts": a.tdp_watts, "description": a.description}
            for a in accs]}

    accs = AIIndustryOntology.get_all_accelerators()
    return {k: {"name": v.name, "vendor": v.vendor.value,
                "bf16_tflops": v.compute.bf16_tflops,
                "memory_gb": v.memory.capacity_gb,
                "memory_type": v.memory.type,
                "tdp_watts": v.tdp_watts}
            for k, v in accs.items()}


@router.get("/ai/accelerators/{name}")
def get_accelerator(name: str):
    """AI 가속기 상세 사양"""
    acc = AIIndustryOntology.get_accelerator(name)
    if not acc:
        raise HTTPException(404, f"Accelerator not found: {name}")
    return acc


@router.get("/ai/hbm")
def list_hbm():
    """HBM 세대별 사양"""
    return AIIndustryOntology.get_all_hbm()


@router.get("/ai/hardware-estimator")
def estimate_hardware(
    model_params_billion: float = Query(..., description="Model parameter count (billions)"),
    precision: str = Query(default="INT8"),
):
    """AI 모델 추론 하드웨어 추정"""
    return AIIndustryOntology.estimate_inference_hardware(
        model_params_billion, precision
    )


@router.get("/ai/models")
def list_ai_models():
    """주요 AI 모델 사양"""
    models = AIIndustryOntology.get_all_models()
    return {k: {"name": v.name, "vendor": v.vendor,
                "params_billion": v.parameter_count_billion,
                "architecture": v.architecture,
                "inference_memory_int8_gb": v.inference_memory_int8_gb}
            for k, v in models.items()}


@router.get("/ai/workload-profiles")
def list_workload_profiles():
    """워크로드 특성 프로파일"""
    return AIIndustryOntology.get_workload_profiles()


# ============================================================
# Materials
# ============================================================

@router.get("/materials")
def list_materials(
    category: Optional[str] = None,
    critical_only: bool = False,
    high_risk_only: bool = False,
):
    """반도체 소재 목록"""
    if critical_only:
        mats = MaterialsKnowledgeBase.get_critical_materials()
    elif high_risk_only:
        mats = MaterialsKnowledgeBase.get_high_risk_materials()
    elif category:
        from app.ontology.materials import MaterialCategory
        try:
            cat = MaterialCategory(category)
            mats = MaterialsKnowledgeBase.get_by_category(cat)
        except ValueError:
            raise HTTPException(400, f"Unknown category: {category}")
    else:
        mats = list(MaterialsKnowledgeBase.get_all_materials().values())

    return {
        "count": len(mats),
        "materials": [
            {"name": m.name, "category": m.category.value,
             "criticality": m.criticality.value,
             "supply_risk": m.supply_risk.value,
             "geographic_concentration": m.geographic_concentration,
             "major_suppliers": m.major_suppliers,
             "description": m.description}
            for m in mats
        ]
    }


@router.get("/materials/japan-dependent")
def get_japan_dependent_materials():
    """일본 의존도 높은 소재 (수출규제 관련)"""
    mats = MaterialsKnowledgeBase.get_japan_dependent()
    return {"count": len(mats), "materials": [
        {"name": m.name, "category": m.category.value,
         "geographic_concentration": m.geographic_concentration,
         "major_suppliers": m.major_suppliers}
        for m in mats]}


@router.get("/materials/export-controlled")
def get_export_controlled_materials():
    """수출 통제 대상 소재"""
    mats = MaterialsKnowledgeBase.get_export_controlled()
    return {"count": len(mats), "materials": [
        {"name": m.name, "description": m.description}
        for m in mats]}


# ============================================================
# Equipment
# ============================================================

@router.get("/equipment")
def list_equipment(category: Optional[str] = None):
    """장비 목록"""
    if category:
        from app.ontology.equipment import EquipCategory
        try:
            cat = EquipCategory(category)
            equips = EquipmentKnowledgeBase.get_by_category(cat)
        except ValueError:
            raise HTTPException(400, f"Unknown category: {category}")
        return {"count": len(equips), "equipment": [
            {"name": e.name, "vendor": e.vendor.name,
             "throughput_wph": e.throughput_wph,
             "price_million_usd": e.purchase_price_million_usd,
             "mtbf_hours": e.mtbf_hours}
            for e in equips]}

    equips = EquipmentKnowledgeBase.get_all_equipment()
    return {k: {"name": v.name, "vendor": v.vendor.name,
                "category": v.category.value,
                "throughput_wph": v.throughput_wph,
                "price_million_usd": v.purchase_price_million_usd}
            for k, v in equips.items()}


@router.get("/equipment/{model_key}")
def get_equipment(model_key: str):
    """장비 상세 사양"""
    equip = EquipmentKnowledgeBase.get_equipment(model_key)
    if not equip:
        raise HTTPException(404, f"Equipment not found: {model_key}")
    return equip


@router.get("/equipment/vendor-share/{category}")
def get_vendor_market_share(category: str):
    """장비 카테고리별 벤더 점유율"""
    from app.ontology.equipment import EquipCategory
    try:
        cat = EquipCategory(category)
    except ValueError:
        raise HTTPException(400, f"Unknown category: {category}")
    return EquipmentKnowledgeBase.get_vendor_market_share(cat)


@router.get("/equipment/fab-cost-estimator")
def estimate_fab_cost(
    node_nm: int = Query(..., description="Process node (nm)"),
    wspm: int = Query(default=50000, description="Wafer starts per month"),
):
    """Fab 장비 투자비 추정"""
    return EquipmentKnowledgeBase.estimate_fab_equipment_cost(node_nm, wspm)


# ============================================================
# Process Flow
# ============================================================

@router.get("/process-flow")
def get_process_flow(module: Optional[str] = None):
    """표준 공정 흐름"""
    if module == "FEOL":
        steps = ProcessFlowOntology.get_feol_steps()
    elif module == "MOL":
        steps = ProcessFlowOntology.get_mol_steps()
    elif module == "BEOL":
        steps = ProcessFlowOntology.get_beol_steps()
    else:
        steps = ProcessFlowOntology.get_ordered_flow()

    return {
        "count": len(steps),
        "steps": [
            {"step_id": s.step_id, "name": s.name,
             "module": s.module.value, "order": s.order,
             "equipment_type": s.equipment_type,
             "yield_impact": s.yield_impact,
             "description": s.description}
            for s in steps
        ]
    }


@router.get("/process-flow/{step_id}")
def get_process_step(step_id: str):
    """공정 단계 상세"""
    step = ProcessFlowOntology.get_step(step_id)
    if not step:
        raise HTTPException(404, f"Step not found: {step_id}")
    return step


@router.get("/process-flow/node-complexity/{node}")
def get_node_complexity(node: str):
    """노드별 공정 복잡도"""
    complexity = ProcessFlowOntology.get_node_complexity(node)
    if not complexity:
        raise HTTPException(404, f"Node not found: {node}")
    return {"node": node, **complexity}


# ============================================================
# Failure Modes
# ============================================================

@router.get("/failure-modes/defects")
def list_defect_types(process_step: Optional[str] = None):
    """결함 유형 목록"""
    if process_step:
        defects = FailureModeOntology.get_defects_for_process(process_step)
    else:
        defects = list(FailureModeOntology.get_all_defect_types().values())

    return {
        "count": len(defects),
        "defects": [
            {"defect_id": d.defect_id, "name": d.name, "name_kr": d.name_kr,
             "category": d.category, "severity": d.severity.value,
             "yield_impact_pct": d.yield_impact_pct,
             "kill_ratio_pct": d.kill_ratio_pct,
             "common_causes": d.common_causes}
            for d in defects
        ]
    }


@router.get("/failure-modes/equipment/{equipment_type}")
def get_equipment_failure_modes(equipment_type: str):
    """장비 유형별 고장 모드"""
    modes = FailureModeOntology.get_failure_modes_for_equipment(equipment_type.upper())
    return {
        "equipment_type": equipment_type,
        "failure_modes": [
            {"mode_id": m.mode_id, "name": m.name_kr,
             "failure_rate_per_1000h": m.failure_rate_per_1000h,
             "mtbf_hours": m.mtbf_hours,
             "early_warning_signs": m.early_warning_signs,
             "preventive_measure": m.preventive_measure}
            for m in modes
        ],
        "early_warning_signs": FailureModeOntology.get_early_warning_signs(equipment_type.upper())
    }
