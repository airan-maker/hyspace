"""
Graph API - Neo4j 그래프 데이터베이스 REST API

마이그레이션, 질의, 시각화 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from ..neo4j_client import Neo4jClient
from ..services.graph_migrator import GraphMigrator
from ..services.graph_query_service import GraphQueryService

router = APIRouter(prefix="/graph")


# ─────────────────────────────────────────────────────
# 관리 엔드포인트
# ─────────────────────────────────────────────────────


@router.get("/status")
async def graph_status():
    """Neo4j 그래프 상태 (노드/관계 통계)"""
    if not Neo4jClient.is_available():
        return {"available": False, "message": "Neo4j is not connected"}
    return Neo4jClient.get_stats()


@router.post("/migrate")
async def migrate_ontology():
    """온톨로지 → Neo4j 전체 마이그레이션 실행"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    migrator = GraphMigrator()
    stats = migrator.migrate_all()
    return {"status": "completed", "stats": stats}


class CypherRequest(BaseModel):
    cypher: str
    params: Optional[dict] = None


@router.post("/query")
async def run_cypher(request: CypherRequest):
    """Cypher 직접 실행 (개발용)"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    results = GraphQueryService.run_custom_cypher(request.cypher, request.params)
    return {"results": results, "count": len(results)}


# ─────────────────────────────────────────────────────
# AI 가속기 질의
# ─────────────────────────────────────────────────────


@router.get("/accelerator/{name}/context")
async def accelerator_full_context(name: str):
    """
    가속기 전체 컨텍스트: 공정, 메모리, 패키징, 호환 모델, 경쟁사

    예: /graph/accelerator/H100/context
    """
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    result = GraphQueryService.get_accelerator_full_context(name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Accelerator '{name}' not found")
    return result


@router.get("/accelerator/{name}/supply-risks")
async def accelerator_supply_risks(name: str):
    """
    가속기에 영향을 주는 공급망 리스크 (다중 홉 질의)

    예: /graph/accelerator/H100/supply-risks
    → H100 → TSMC N4P → 공정 → 소재 → 리스크
    """
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    results = GraphQueryService.get_supply_chain_risks_for_accelerator(name)
    return {"accelerator": name, "risks": results, "count": len(results)}


@router.get("/accelerator/compare")
async def compare_accelerators(names: str = Query(..., description="쉼표 구분 키 목록 (예: H100_SXM,MI300X,B200)")):
    """가속기 비교"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    name_list = [n.strip() for n in names.split(",")]
    results = GraphQueryService.get_accelerator_comparison(name_list)
    return {"accelerators": results}


# ─────────────────────────────────────────────────────
# 공정 & 수율 질의
# ─────────────────────────────────────────────────────


@router.get("/process-flow")
async def process_flow_with_risks():
    """공정 플로우 + 각 단계별 결함/장비/소재 리스크"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    results = GraphQueryService.get_process_flow_with_risks()
    return {"steps": results}


@router.get("/process-flow/high-risk")
async def high_risk_steps():
    """수율 영향 HIGH인 공정 단계 + 관련 리스크"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    results = GraphQueryService.get_high_risk_process_steps()
    return {"high_risk_steps": results}


# ─────────────────────────────────────────────────────
# 장비 분석
# ─────────────────────────────────────────────────────


@router.get("/equipment/{name}/impact")
async def equipment_impact(name: str):
    """
    장비 고장 시 영향 분석

    예: /graph/equipment/ASML/impact
    """
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    result = GraphQueryService.get_equipment_impact_analysis(name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Equipment '{name}' not found")
    return result


# ─────────────────────────────────────────────────────
# 소재 공급망 분석
# ─────────────────────────────────────────────────────


@router.get("/material/{name}/dependency")
async def material_dependency(name: str):
    """
    소재 의존성 체인: 소재 → 공정 → 장비 → 고장모드

    예: /graph/material/EUV/dependency
    """
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    result = GraphQueryService.get_material_dependency_chain(name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Material '{name}' not found")
    return result


@router.get("/materials/critical-risks")
async def critical_supply_risks():
    """공급 리스크가 HIGH 이상인 소재 목록 + 영향 범위"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    results = GraphQueryService.get_critical_supply_risks()
    return {"materials": results, "count": len(results)}


# ─────────────────────────────────────────────────────
# 경로 탐색 & 시각화
# ─────────────────────────────────────────────────────


@router.get("/path")
async def find_path(
    from_entity: str = Query(..., alias="from", description="시작 엔티티 이름"),
    to_entity: str = Query(..., alias="to", description="끝 엔티티 이름"),
    max_hops: int = Query(5, description="최대 홉 수"),
):
    """
    두 엔티티 간 최단 경로 탐색

    예: /graph/path?from=H100&to=EUV Photoresist
    """
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    results = GraphQueryService.find_path_between(from_entity, to_entity, max_hops)
    return {"paths": results, "count": len(results)}


@router.get("/visualization")
async def graph_visualization():
    """
    전체 그래프 시각화 데이터 (force-graph 호환)

    반환: {nodes: [...], links: [...]}
    """
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    return GraphQueryService.get_all_nodes_for_visualization()
