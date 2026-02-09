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
from ..services.graph_search_service import search_graph_nodes, get_available_labels

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


# ─────────────────────────────────────────────────────
# Research Agent 확장 엔드포인트
# ─────────────────────────────────────────────────────


@router.get("/foundry/overview")
async def foundry_overview():
    """파운드리 기업 + 팹 사이트 + 공정 노드 전체 조회"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    try:
        from research_agent.graph.migrator_ext import ResearchGraphQueryService
        results = ResearchGraphQueryService.get_foundry_overview()
        return {"foundries": results, "count": len(results)}
    except ImportError:
        raise HTTPException(status_code=501, detail="Research agent not installed")


@router.get("/accelerator/{name}/supply-chain-map")
async def supply_chain_full_map(name: str):
    """
    가속기 전체 공급망 맵 (5+ hop)

    가속기 → 설계사 → 공정 → 파운드리 → 팹 → 메모리공급사 → 인터커넥트 → 응용 → 쿨링
    """
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    try:
        from research_agent.graph.migrator_ext import ResearchGraphQueryService
        results = ResearchGraphQueryService.get_supply_chain_full_map(name)
        return {"supply_chain": results}
    except ImportError:
        raise HTTPException(status_code=501, detail="Research agent not installed")


@router.get("/regulations")
async def regulation_impact():
    """규제/정책 영향 분석"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    try:
        from research_agent.graph.migrator_ext import ResearchGraphQueryService
        results = ResearchGraphQueryService.get_regulation_impact("")
        return {"regulations": results, "count": len(results)}
    except ImportError:
        raise HTTPException(status_code=501, detail="Research agent not installed")


@router.get("/status/extended")
async def graph_status_extended():
    """확장된 그래프 통계 (Tier 1/2/3 분류 포함)"""
    try:
        from research_agent.graph.migrator_ext import ResearchGraphQueryService
        return ResearchGraphQueryService.get_graph_overview_extended()
    except ImportError:
        if not Neo4jClient.is_available():
            return {"available": False}
        return Neo4jClient.get_stats()


# ─────────────────────────────────────────────────────
# 검색 & 필터링
# ─────────────────────────────────────────────────────


@router.get("/search")
async def search_nodes(
    q: Optional[str] = Query(None, description="검색 키워드"),
    label: Optional[str] = Query(None, description="노드 라벨 필터"),
    risk: Optional[str] = Query(None, description="리스크 레벨 필터 (HIGH, CRITICAL 등)"),
    limit: int = Query(20, ge=1, le=100, description="결과 수 제한"),
):
    """그래프 노드 검색"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    results = search_graph_nodes(query=q, label=label, risk=risk, limit=limit)
    return {"results": results, "count": len(results)}


@router.get("/labels")
async def get_labels():
    """사용 가능한 노드 라벨 목록"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    labels = get_available_labels()
    return {"labels": labels}


@router.get("/template-options")
async def get_template_options():
    """질의 템플릿에 사용할 드롭다운 옵션 목록 (가속기, 장비 벤더, 소재, 전체 노드)"""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    session = Neo4jClient.get_session()
    if not session:
        return {"accelerators": [], "equipment_vendors": [], "materials": [], "all_nodes": []}

    with session:
        acc_result = session.run(
            "MATCH (a:AIAccelerator) RETURN a.name AS name ORDER BY a.name"
        )
        accelerators = [r["name"] for r in acc_result if r["name"]]

        eq_result = session.run(
            "MATCH (e:Equipment) RETURN DISTINCT e.vendor AS vendor ORDER BY e.vendor"
        )
        equipment_vendors = [r["vendor"] for r in eq_result if r["vendor"]]

        mat_result = session.run(
            "MATCH (m:Material) RETURN m.name AS name ORDER BY m.name"
        )
        materials = [r["name"] for r in mat_result if r["name"]]

        all_result = session.run(
            "MATCH (n) WHERE n.name IS NOT NULL RETURN DISTINCT n.name AS name ORDER BY n.name"
        )
        all_nodes = [r["name"] for r in all_result if r["name"]]

    return {
        "accelerators": accelerators,
        "equipment_vendors": equipment_vendors,
        "materials": materials,
        "all_nodes": all_nodes,
    }


# ─────────────────────────────────────────────────────
# 지리공간 데이터
# ─────────────────────────────────────────────────────

# 주요 반도체 소재 공급처 위치 매핑 (실제 지리 좌표)
SUPPLIER_LOCATIONS = {
    "ASML": {"lat": 51.4416, "lng": 5.4697, "country": "Netherlands", "city": "Veldhoven"},
    "TSMC": {"lat": 24.7736, "lng": 120.9820, "country": "Taiwan", "city": "Hsinchu"},
    "Samsung": {"lat": 37.2636, "lng": 127.0286, "country": "South Korea", "city": "Hwaseong"},
    "Intel": {"lat": 45.3428, "lng": -122.8364, "country": "USA", "city": "Hillsboro"},
    "Applied Materials": {"lat": 37.3844, "lng": -121.9792, "country": "USA", "city": "Santa Clara"},
    "Tokyo Electron": {"lat": 35.6762, "lng": 139.6503, "country": "Japan", "city": "Tokyo"},
    "Shin-Etsu": {"lat": 36.2048, "lng": 137.2529, "country": "Japan", "city": "Takefu"},
    "JSR": {"lat": 35.6762, "lng": 139.6503, "country": "Japan", "city": "Tokyo"},
    "SK Hynix": {"lat": 37.2494, "lng": 127.0030, "country": "South Korea", "city": "Icheon"},
    "Micron": {"lat": 43.6150, "lng": -116.2023, "country": "USA", "city": "Boise"},
    "SUMCO": {"lat": 33.5902, "lng": 130.4017, "country": "Japan", "city": "Fukuoka"},
    "Entegris": {"lat": 44.9778, "lng": -93.2650, "country": "USA", "city": "Minneapolis"},
    "Air Liquide": {"lat": 48.8566, "lng": 2.3522, "country": "France", "city": "Paris"},
    "Linde": {"lat": 48.1351, "lng": 11.5820, "country": "Germany", "city": "Munich"},
    "DuPont": {"lat": 39.7391, "lng": -75.5398, "country": "USA", "city": "Wilmington"},
    "Nikon": {"lat": 35.6762, "lng": 139.6503, "country": "Japan", "city": "Tokyo"},
    "KLA": {"lat": 37.0471, "lng": -121.5782, "country": "USA", "city": "Milpitas"},
    "Lam Research": {"lat": 37.3688, "lng": -122.0363, "country": "USA", "city": "Fremont"},
}


@router.get("/geospatial/suppliers")
async def get_supplier_geospatial():
    """소재/장비 공급처의 지리공간 데이터를 반환합니다."""

    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    suppliers = []

    with Neo4jClient.get_session() as session:
        # 장비/소재에서 vendor 정보 추출
        result = session.run("""
            MATCH (n)
            WHERE n.vendor IS NOT NULL
            RETURN n.vendor as vendor, labels(n) as nodeLabels, n.name as name,
                   n.supply_risk as risk, n.criticality as criticality,
                   count(*) as count
            ORDER BY count DESC
        """)

        seen_vendors = set()
        for record in result:
            vendor = record["vendor"]
            if not vendor or vendor in seen_vendors:
                continue
            seen_vendors.add(vendor)

            # 위치 매핑 (부분 매칭)
            location = None
            for key, loc in SUPPLIER_LOCATIONS.items():
                if key.lower() in vendor.lower() or vendor.lower() in key.lower():
                    location = loc
                    break

            if location:
                suppliers.append({
                    "vendor": vendor,
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "country": location["country"],
                    "city": location["city"],
                    "node_label": record["nodeLabels"][0] if record["nodeLabels"] else "Unknown",
                    "node_name": record["name"],
                    "risk": record["risk"],
                    "criticality": record["criticality"],
                })

    return {"suppliers": suppliers, "count": len(suppliers)}
