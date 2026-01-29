from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import ProcessNode, IPBlock
from ..schemas import ProcessNodeResponse, IPBlockResponse

router = APIRouter()


@router.get("/process-nodes", response_model=list[ProcessNodeResponse])
async def get_process_nodes(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    공정 노드 목록 조회

    지원하는 반도체 공정 노드 목록을 반환합니다.
    """
    query = db.query(ProcessNode)
    if active_only:
        query = query.filter(ProcessNode.is_active == True)
    nodes = query.order_by(ProcessNode.node_nm).all()

    # 데이터가 없으면 기본 데이터 반환
    if not nodes:
        return [
            ProcessNodeResponse(
                id=1, name="3nm", node_nm=3, wafer_cost=20000,
                defect_density=0.12, base_core_area=0.50,
                cache_density=0.35, io_area_per_lane=0.25,
                power_density=0.45, max_frequency_ghz=4.0, is_active=True
            ),
            ProcessNodeResponse(
                id=2, name="5nm", node_nm=5, wafer_cost=16000,
                defect_density=0.08, base_core_area=0.65,
                cache_density=0.45, io_area_per_lane=0.30,
                power_density=0.40, max_frequency_ghz=3.5, is_active=True
            ),
            ProcessNodeResponse(
                id=3, name="7nm", node_nm=7, wafer_cost=10000,
                defect_density=0.05, base_core_area=0.85,
                cache_density=0.60, io_area_per_lane=0.38,
                power_density=0.35, max_frequency_ghz=3.0, is_active=True
            ),
        ]

    return [ProcessNodeResponse.model_validate(node) for node in nodes]


@router.get("/process-nodes/{node_id}", response_model=ProcessNodeResponse)
async def get_process_node(
    node_id: int,
    db: Session = Depends(get_db)
):
    """
    공정 노드 상세 조회
    """
    node = db.query(ProcessNode).filter(ProcessNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Process node not found")
    return ProcessNodeResponse.model_validate(node)


@router.get("/ip-library", response_model=list[IPBlockResponse])
async def get_ip_library(
    ip_type: Optional[str] = None,
    silicon_proven: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    IP 라이브러리 조회

    사용 가능한 IP 블록(CPU, GPU, NPU 등) 목록을 반환합니다.
    """
    query = db.query(IPBlock)

    if ip_type:
        query = query.filter(IPBlock.type == ip_type)
    if silicon_proven is not None:
        query = query.filter(IPBlock.silicon_proven == silicon_proven)

    blocks = query.order_by(IPBlock.type, IPBlock.name).all()

    # 데이터가 없으면 기본 데이터 반환
    if not blocks:
        return [
            IPBlockResponse(
                id=1, name="Cortex-A78", type="CPU", vendor="ARM",
                version="r1p0", area_mm2=0.65, power_mw=750,
                performance_metric=3.0, performance_unit="GHz",
                silicon_proven=True, compatible_nodes=[3, 5, 7],
                description="High-performance CPU core"
            ),
            IPBlockResponse(
                id=2, name="Cortex-A55", type="CPU", vendor="ARM",
                version="r1p0", area_mm2=0.25, power_mw=200,
                performance_metric=2.0, performance_unit="GHz",
                silicon_proven=True, compatible_nodes=[3, 5, 7],
                description="Efficiency CPU core"
            ),
            IPBlockResponse(
                id=3, name="Mali-G78", type="GPU", vendor="ARM",
                version="MP24", area_mm2=2.1, power_mw=2500,
                performance_metric=1.5, performance_unit="TFLOPS",
                silicon_proven=True, compatible_nodes=[5, 7],
                description="High-performance mobile GPU"
            ),
            IPBlockResponse(
                id=4, name="NPU-V2", type="NPU", vendor="Internal",
                version="2.0", area_mm2=1.8, power_mw=1200,
                performance_metric=8.0, performance_unit="TOPS",
                silicon_proven=True, compatible_nodes=[3, 5],
                description="Neural processing unit for AI inference"
            ),
            IPBlockResponse(
                id=5, name="DDR5-Controller", type="MEMORY_CTRL", vendor="Synopsys",
                version="1.0", area_mm2=3.0, power_mw=500,
                performance_metric=6400, performance_unit="MT/s",
                silicon_proven=True, compatible_nodes=[3, 5, 7],
                description="DDR5 memory controller"
            ),
        ]

    return [IPBlockResponse.model_validate(block) for block in blocks]


@router.get("/ip-library/{ip_id}", response_model=IPBlockResponse)
async def get_ip_block(
    ip_id: int,
    db: Session = Depends(get_db)
):
    """
    IP 블록 상세 조회
    """
    block = db.query(IPBlock).filter(IPBlock.id == ip_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="IP block not found")
    return IPBlockResponse.model_validate(block)
