"""
Seed Data API

온톨로지 기반 시드 데이터 생성 및 DB 로딩 API.
시나리오 선택 → 미리보기 → DB 적용 워크플로우.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.seed_data_agent import SeedDataAgent, SCENARIOS
from app.services.seed_data_loader import SeedDataLoader

router = APIRouter(prefix="/seed", tags=["Seed Data Agent"])


@router.get("/scenarios")
def list_scenarios():
    """사용 가능한 시드 데이터 시나리오 목록"""
    return {
        "count": len(SCENARIOS),
        "scenarios": SeedDataAgent.list_scenarios(),
    }


@router.get("/scenarios/{scenario_id}")
def get_scenario_detail(scenario_id: str):
    """시나리오 상세 정보"""
    if scenario_id not in SCENARIOS:
        raise HTTPException(404, f"Scenario not found: {scenario_id}")

    scenario = SCENARIOS[scenario_id]
    return {
        "scenario_id": scenario.scenario_id,
        "name": scenario.name,
        "name_kr": scenario.name_kr,
        "description": scenario.description,
        "process_node": scenario.process_node,
        "target_product": scenario.target_product,
        "wspm": scenario.wspm,
        "equipment_count": scenario.equipment_count,
        "wip_lots": scenario.wip_lots,
        "supply_chain_tiers": scenario.supply_chain_tiers,
        "history_days": scenario.history_days,
        "tags": scenario.tags,
    }


@router.post("/preview/{scenario_id}")
def preview_seed_data(scenario_id: str):
    """
    시드 데이터 미리보기 (DB에 저장하지 않음).

    온톨로지 기반으로 생성될 데이터를 미리 확인합니다.
    각 엔티티 타입별 샘플과 총 개수를 반환합니다.
    """
    try:
        agent = SeedDataAgent(scenario_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

    data = agent.generate_all()

    # 미리보기: 각 카테고리별 첫 3개만 + 총 개수
    preview = {
        "scenario": data["scenario"],
        "summary": data["summary"],
    }

    for key in ["process_nodes", "ip_blocks", "fab_equipment",
                "wip_items", "materials", "suppliers",
                "wafer_records", "yield_events"]:
        items = data.get(key, [])
        preview[key] = {
            "total_count": len(items),
            "sample": items[:3],
        }

    return preview


@router.post("/apply/{scenario_id}")
def apply_seed_data(
    scenario_id: str,
    clear_existing: bool = Query(
        default=False,
        description="기존 데이터를 삭제하고 새로 생성 (True: 초기화, False: 추가)"
    ),
    db: Session = Depends(get_db),
):
    """
    시드 데이터를 DB에 적용합니다.

    - clear_existing=False (기본): 기존 데이터에 추가
    - clear_existing=True: 기존 데이터 삭제 후 새로 생성
    """
    try:
        agent = SeedDataAgent(scenario_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

    data = agent.generate_all()
    loader = SeedDataLoader(db)

    try:
        result = loader.load_all(data, clear_existing=clear_existing)
        return {
            "status": "success",
            "scenario": data["scenario"],
            "loaded": result,
            "message": f"Seed data for '{SCENARIOS[scenario_id].name_kr}' applied successfully.",
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to load seed data: {str(e)}")


@router.delete("/clear")
def clear_all_seed_data(
    confirm: bool = Query(
        ..., description="반드시 True를 전달해야 삭제가 진행됩니다"
    ),
    db: Session = Depends(get_db),
):
    """모든 시드 데이터 삭제 (주의: 되돌릴 수 없습니다)"""
    if not confirm:
        raise HTTPException(400, "Set confirm=true to proceed with deletion")

    loader = SeedDataLoader(db)
    result = loader.clear_all()
    return {
        "status": "cleared",
        "deleted": result,
    }


@router.get("/status")
def get_seed_data_status(db: Session = Depends(get_db)):
    """현재 DB의 시드 데이터 상태 확인"""
    loader = SeedDataLoader(db)
    return loader.get_status()
