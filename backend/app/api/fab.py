"""
Virtual Fab API Endpoints

가상 팹 디지털 트윈 API
병목 예측, What-If 시뮬레이션
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.virtual_fab import VirtualFabSimulator, WhatIfScenarioEngine, BottleneckPredictor
from app.services.audit_logger import AuditLogger
from app.models.fab import FabEquipment, WIPItem, SimulationScenario, Bottleneck, MaintenanceSchedule

router = APIRouter(prefix="/fab", tags=["Virtual Fab"])


# ==================== Schemas ====================

class EquipmentCreate(BaseModel):
    equipment_id: str
    name: str
    equipment_type: str
    bay: Optional[str] = None
    capacity_wph: Optional[float] = None
    mtbf_hours: Optional[float] = None
    mttr_hours: Optional[float] = None
    specs: Optional[dict] = None


class EquipmentResponse(BaseModel):
    id: int
    equipment_id: str
    name: str
    equipment_type: str
    bay: Optional[str]
    capacity_wph: Optional[float]
    oee: Optional[float]
    availability: Optional[float]
    mtbf_hours: Optional[float]
    mttr_hours: Optional[float]
    status: Optional[str]
    current_recipe: Optional[str]
    current_lot_id: Optional[str]
    last_maintenance: Optional[datetime]
    next_maintenance: Optional[datetime]

    class Config:
        from_attributes = True


class WIPCreate(BaseModel):
    lot_id: str
    product_id: str
    wafer_count: int
    current_step: int = 1
    total_steps: int
    priority: int = 5
    due_date: Optional[datetime] = None
    route: Optional[list] = None


class WIPResponse(BaseModel):
    id: int
    lot_id: str
    product_id: str
    wafer_count: int
    current_step: int
    total_steps: int
    current_operation: Optional[str]
    priority: int
    due_date: Optional[datetime]
    estimated_completion: Optional[datetime]
    current_bay: Optional[str]
    current_queue: Optional[str]
    status: Optional[str]

    class Config:
        from_attributes = True


class ScenarioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scenario_type: str = Field(..., description="EQUIPMENT_FAILURE, DEMAND_SPIKE, NEW_PROCESS, MAINTENANCE")
    parameters: dict


class ScenarioResponse(BaseModel):
    id: int
    scenario_id: str
    name: str
    description: Optional[str]
    scenario_type: str
    parameters: dict
    status: str
    baseline_metrics: Optional[dict]
    scenario_metrics: Optional[dict]
    impact_analysis: Optional[dict]
    recommendations: Optional[list]
    confidence_score: Optional[float]
    created_at: datetime
    executed_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SimulationRequest(BaseModel):
    duration_hours: float = Field(default=168, ge=1, le=720, description="시뮬레이션 기간 (시간)")
    num_equipments: int = Field(default=20, ge=5, le=100, description="장비 수")
    num_lots: int = Field(default=50, ge=10, le=500, description="Lot 수")


class FabStatusResponse(BaseModel):
    total_equipment: int
    equipment_by_status: dict
    total_wip: int
    wip_by_status: dict
    current_throughput: float
    avg_oee: float
    active_bottlenecks: int


# ==================== Fab Status ====================

@router.get("/status", response_model=FabStatusResponse)
def get_fab_status(db: Session = Depends(get_db)):
    """
    현재 팹 상태 조회

    장비 상태, WIP 현황, 주요 지표 요약
    """
    # 장비 상태
    equipments = db.query(FabEquipment).all()
    equipment_by_status = {}
    total_oee = 0
    oee_count = 0

    for eq in equipments:
        status = eq.status or "UNKNOWN"
        equipment_by_status[status] = equipment_by_status.get(status, 0) + 1
        if eq.oee:
            total_oee += eq.oee
            oee_count += 1

    # WIP 상태
    wips = db.query(WIPItem).all()
    wip_by_status = {}
    for wip in wips:
        status = wip.status or "UNKNOWN"
        wip_by_status[status] = wip_by_status.get(status, 0) + 1

    # 병목 수
    bottlenecks = db.query(Bottleneck).filter(
        Bottleneck.status == "PREDICTED"
    ).count()

    return FabStatusResponse(
        total_equipment=len(equipments),
        equipment_by_status=equipment_by_status,
        total_wip=len(wips),
        wip_by_status=wip_by_status,
        current_throughput=len(wips) * 0.5,  # 데모 값
        avg_oee=total_oee / oee_count if oee_count > 0 else 85.0,
        active_bottlenecks=bottlenecks
    )


# ==================== Equipment ====================

@router.post("/equipment", response_model=EquipmentResponse)
def create_equipment(
    equipment: EquipmentCreate,
    db: Session = Depends(get_db)
):
    """장비 등록"""
    db_equipment = FabEquipment(
        equipment_id=equipment.equipment_id,
        name=equipment.name,
        equipment_type=equipment.equipment_type,
        bay=equipment.bay,
        capacity_wph=equipment.capacity_wph,
        mtbf_hours=equipment.mtbf_hours,
        mttr_hours=equipment.mttr_hours,
        specs=equipment.specs,
        status="IDLE"
    )

    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)

    return db_equipment


@router.get("/equipment", response_model=list[EquipmentResponse])
def get_equipment_list(
    equipment_type: Optional[str] = None,
    bay: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """장비 목록 조회"""
    query = db.query(FabEquipment)

    if equipment_type:
        query = query.filter(FabEquipment.equipment_type == equipment_type)
    if bay:
        query = query.filter(FabEquipment.bay == bay)
    if status:
        query = query.filter(FabEquipment.status == status)

    return query.offset(skip).limit(limit).all()


@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """특정 장비 조회"""
    equipment = db.query(FabEquipment).filter(
        FabEquipment.equipment_id == equipment_id
    ).first()

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return equipment


# ==================== WIP ====================

@router.post("/wip", response_model=WIPResponse)
def create_wip(
    wip: WIPCreate,
    db: Session = Depends(get_db)
):
    """WIP 등록"""
    db_wip = WIPItem(
        lot_id=wip.lot_id,
        product_id=wip.product_id,
        wafer_count=wip.wafer_count,
        current_step=wip.current_step,
        total_steps=wip.total_steps,
        priority=wip.priority,
        due_date=wip.due_date,
        route=wip.route,
        status="QUEUED"
    )

    db.add(db_wip)
    db.commit()
    db.refresh(db_wip)

    return db_wip


@router.get("/wip", response_model=list[WIPResponse])
def get_wip_list(
    status: Optional[str] = None,
    priority_min: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """WIP 목록 조회"""
    query = db.query(WIPItem)

    if status:
        query = query.filter(WIPItem.status == status)
    if priority_min:
        query = query.filter(WIPItem.priority >= priority_min)

    return query.order_by(WIPItem.priority.desc()).offset(skip).limit(limit).all()


# ==================== Bottleneck Prediction ====================

@router.get("/bottlenecks")
def predict_bottlenecks(
    horizon_hours: int = Query(default=24, ge=1, le=168, description="예측 기간 (시간)"),
    db: Session = Depends(get_db)
):
    """
    병목 예측

    향후 N시간 내 발생 가능한 병목 예측
    """
    predictor = BottleneckPredictor(db)
    predictions = predictor.predict_bottlenecks(horizon_hours)

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="PREDICT",
        resource="bottleneck",
        details={"horizon_hours": horizon_hours, "predictions_count": len(predictions)}
    )

    return {
        "horizon_hours": horizon_hours,
        "prediction_time": datetime.utcnow().isoformat(),
        "predictions": predictions
    }


# ==================== Simulation ====================

@router.post("/simulate")
def run_simulation(
    request: SimulationRequest,
    db: Session = Depends(get_db)
):
    """
    팹 시뮬레이션 실행

    지정된 기간 동안 팹 운영 시뮬레이션 및 결과 반환
    """
    simulator = VirtualFabSimulator(db)
    simulator.initialize_demo_fab(
        num_equipments=request.num_equipments,
        num_lots=request.num_lots
    )

    metrics = simulator.run(duration_hours=request.duration_hours)

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="SIMULATE",
        resource="fab",
        details={
            "duration_hours": request.duration_hours,
            "lots_completed": metrics.total_lots_completed
        }
    )

    return {
        "simulation_parameters": {
            "duration_hours": request.duration_hours,
            "num_equipments": request.num_equipments,
            "num_lots": request.num_lots
        },
        "results": {
            "total_lots_completed": metrics.total_lots_completed,
            "total_wafers_completed": metrics.total_wafers_completed,
            "avg_cycle_time_hours": round(metrics.avg_cycle_time_hours, 2),
            "throughput_lots_per_day": round(metrics.throughput_lots_per_day, 2),
            "throughput_wafers_per_day": round(metrics.throughput_wafers_per_day, 2),
            "equipment_utilization": metrics.equipment_utilization,
            "bottleneck_equipment": metrics.bottleneck_equipment
        }
    }


# ==================== What-If Scenarios ====================

@router.post("/scenarios", response_model=ScenarioResponse)
def create_scenario(
    scenario: ScenarioCreate,
    db: Session = Depends(get_db)
):
    """
    What-If 시나리오 생성

    시나리오 유형:
    - EQUIPMENT_FAILURE: 장비 고장
    - DEMAND_SPIKE: 수요 급증
    - NEW_PROCESS: 신규 공정 도입
    - MAINTENANCE: 유지보수
    """
    engine = WhatIfScenarioEngine(db)

    db_scenario = engine.create_scenario(
        name=scenario.name,
        scenario_type=scenario.scenario_type,
        parameters=scenario.parameters,
        description=scenario.description,
        created_by="system"
    )

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="CREATE",
        resource="scenario",
        resource_id=db_scenario.scenario_id,
        details={"type": scenario.scenario_type}
    )

    return db_scenario


@router.get("/scenarios", response_model=list[ScenarioResponse])
def get_scenarios(
    status: Optional[str] = None,
    scenario_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """시나리오 목록 조회"""
    query = db.query(SimulationScenario)

    if status:
        query = query.filter(SimulationScenario.status == status)
    if scenario_type:
        query = query.filter(SimulationScenario.scenario_type == scenario_type)

    return query.order_by(SimulationScenario.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(
    scenario_id: str,
    db: Session = Depends(get_db)
):
    """특정 시나리오 조회"""
    scenario = db.query(SimulationScenario).filter(
        SimulationScenario.scenario_id == scenario_id
    ).first()

    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return scenario


@router.post("/scenarios/{scenario_id}/run")
def run_scenario(
    scenario_id: str,
    duration_hours: float = Query(default=168, ge=24, le=720),
    db: Session = Depends(get_db)
):
    """
    시나리오 실행

    베이스라인 대비 시나리오 영향 분석
    """
    engine = WhatIfScenarioEngine(db)

    try:
        result = engine.run_scenario(scenario_id, duration_hours)

        # 감사 로그
        audit = AuditLogger(db)
        audit.log(
            user_id=0,
            user_role="system",
            action="RUN_SCENARIO",
            resource="scenario",
            resource_id=scenario_id,
            details={"duration_hours": duration_hours}
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


# ==================== Maintenance ====================

@router.get("/maintenance")
def get_maintenance_schedule(
    equipment_id: Optional[str] = None,
    status: Optional[str] = None,
    days_ahead: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """유지보수 일정 조회"""
    from datetime import timedelta

    query = db.query(MaintenanceSchedule)

    if equipment_id:
        query = query.filter(MaintenanceSchedule.equipment_id == equipment_id)
    if status:
        query = query.filter(MaintenanceSchedule.status == status)

    # 향후 N일 내 일정
    end_date = datetime.utcnow() + timedelta(days=days_ahead)
    query = query.filter(MaintenanceSchedule.scheduled_start <= end_date)

    schedules = query.order_by(MaintenanceSchedule.scheduled_start).all()

    return {
        "period_days": days_ahead,
        "schedules": [
            {
                "schedule_id": s.schedule_id,
                "equipment_id": s.equipment_id,
                "maintenance_type": s.maintenance_type,
                "scheduled_start": s.scheduled_start.isoformat() if s.scheduled_start else None,
                "scheduled_end": s.scheduled_end.isoformat() if s.scheduled_end else None,
                "status": s.status,
                "description": s.description,
                "estimated_downtime_hours": s.estimated_downtime_hours
            }
            for s in schedules
        ]
    }
