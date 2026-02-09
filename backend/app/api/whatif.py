"""
What-If Simulation API

시나리오 기반 공급망 영향 분석 엔드포인트
"""

from fastapi import APIRouter, HTTPException

from ..neo4j_client import Neo4jClient
from ..schemas.whatif_schema import (
    WhatIfRequest,
    WhatIfResponse,
    WhatIfPreset,
    ScenarioType,
)
from ..services.whatif_simulator import (
    simulate_equipment_delay,
    simulate_material_shortage,
    simulate_process_delay,
)

router = APIRouter(prefix="/graph")

PRESETS = [
    WhatIfPreset(
        id="euv_delay_3m",
        label="ASML EUV 장비 3개월 지연",
        description="ASML EUV 노광 장비 공급이 3개월 지연될 경우 공정, 소재, 가속기 생산에 미치는 영향",
        scenario_type=ScenarioType.EQUIPMENT_DELAY,
        target_entity="ASML",
        delay_months=3,
    ),
    WhatIfPreset(
        id="euv_resist_shortage",
        label="EUV Photoresist 공급 중단",
        description="EUV 포토레지스트 공급이 6개월간 중단될 경우 전체 공정 영향",
        scenario_type=ScenarioType.MATERIAL_SHORTAGE,
        target_entity="EUV",
        delay_months=6,
    ),
    WhatIfPreset(
        id="neon_crisis",
        label="네온 가스 공급 위기",
        description="지정학적 이유로 네온 가스 공급이 3개월간 제한될 경우",
        scenario_type=ScenarioType.MATERIAL_SHORTAGE,
        target_entity="Neon",
        delay_months=3,
    ),
    WhatIfPreset(
        id="n3p_delay_6m",
        label="TSMC N3P 공정 6개월 지연",
        description="TSMC N3P 공정노드 양산이 6개월 지연될 경우 관련 가속기 영향",
        scenario_type=ScenarioType.PROCESS_DELAY,
        target_entity="N3P",
        delay_months=6,
    ),
    WhatIfPreset(
        id="cmp_slurry_shortage",
        label="CMP 슬러리 공급 부족",
        description="CMP 슬러리 공급이 3개월간 부족할 경우 평탄화 공정 영향",
        scenario_type=ScenarioType.MATERIAL_SHORTAGE,
        target_entity="CMP",
        delay_months=3,
    ),
]


@router.get("/whatif/presets")
async def get_whatif_presets():
    """What-If 시나리오 프리셋 목록"""
    return {"presets": [p.model_dump() for p in PRESETS]}


@router.post("/whatif")
async def execute_whatif(request: WhatIfRequest):
    """What-If 시나리오 실행"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    scenario = {
        "type": request.scenario_type.value,
        "target": request.target_entity,
        "delay_months": request.delay_months,
    }

    if request.scenario_type == ScenarioType.EQUIPMENT_DELAY:
        result = simulate_equipment_delay(request.target_entity, request.delay_months)
    elif request.scenario_type == ScenarioType.MATERIAL_SHORTAGE:
        result = simulate_material_shortage(request.target_entity, request.delay_months)
    elif request.scenario_type == ScenarioType.PROCESS_DELAY:
        result = simulate_process_delay(request.target_entity, request.delay_months)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown scenario type: {request.scenario_type}")

    # AI 내러티브 (선택적)
    narrative = None
    if request.include_ai_narrative:
        try:
            from ..services.ai_insight_service import generate_insight
            narrative = generate_insight("custom", {
                "scenario": scenario,
                "affected_nodes": [n.model_dump() for n in result["affected_nodes"][:15]],
                "total_affected": result["total_affected"],
                "alternatives": result.get("alternatives", []),
            })
        except Exception:
            narrative = None

    return WhatIfResponse(
        scenario=scenario,
        affected_nodes=result["affected_nodes"],
        affected_node_ids=result["affected_node_ids"],
        total_affected=result["total_affected"],
        alternatives=result.get("alternatives", []),
        narrative=narrative,
    )
