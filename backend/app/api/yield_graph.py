"""
Yield-Graph Bridge API

수율 이벤트에서 관련 그래프 컨텍스트를 조회하는 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..neo4j_client import Neo4jClient
from ..services.yield_graph_bridge import get_graph_context_for_event

router = APIRouter(prefix="/graph")


class GraphContextRequest(BaseModel):
    process_step: Optional[str] = None
    equipment_id: Optional[str] = None
    material: Optional[str] = None


@router.post("/context-from-event")
async def get_context_from_event(request: GraphContextRequest):
    """수율 이벤트 정보로부터 관련 그래프 컨텍스트를 조회합니다."""
    if not Neo4jClient.is_available():
        raise HTTPException(status_code=503, detail="Neo4j is not available")

    if not request.process_step and not request.equipment_id and not request.material:
        raise HTTPException(
            status_code=400,
            detail="process_step, equipment_id, material 중 하나 이상 필요합니다",
        )

    result = get_graph_context_for_event(
        process_step=request.process_step,
        equipment_id=request.equipment_id,
        material=request.material,
    )

    return result
