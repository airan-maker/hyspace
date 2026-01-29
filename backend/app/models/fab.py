"""
Virtual Fab Models

가상 팹 디지털 트윈을 위한 데이터 모델
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class EquipmentStatus(str, enum.Enum):
    RUNNING = "RUNNING"
    IDLE = "IDLE"
    MAINTENANCE = "MAINTENANCE"
    DOWN = "DOWN"
    SETUP = "SETUP"


class EquipmentType(str, enum.Enum):
    LITHOGRAPHY = "LITHOGRAPHY"
    ETCHER = "ETCHER"
    CVD = "CVD"
    PVD = "PVD"
    CMP = "CMP"
    IMPLANT = "IMPLANT"
    DIFFUSION = "DIFFUSION"
    METROLOGY = "METROLOGY"
    CLEAN = "CLEAN"
    OTHER = "OTHER"


class FabEquipment(Base):
    """팹 장비 모델"""
    __tablename__ = "fab_equipment"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    equipment_type = Column(String(50), nullable=False)
    bay = Column(String(50))

    # 성능 지표
    capacity_wph = Column(Float)  # Wafers Per Hour
    oee = Column(Float)  # Overall Equipment Effectiveness (0-100)
    availability = Column(Float)  # 가용성 (0-100)
    performance = Column(Float)  # 성능 (0-100)
    quality = Column(Float)  # 품질 (0-100)

    # 신뢰성 지표
    mtbf_hours = Column(Float)  # Mean Time Between Failures
    mttr_hours = Column(Float)  # Mean Time To Repair

    # 상태
    status = Column(String(20), default="IDLE")
    current_recipe = Column(String(100))
    current_lot_id = Column(String(50))

    # 유지보수
    last_maintenance = Column(DateTime)
    next_maintenance = Column(DateTime)
    maintenance_notes = Column(String(500))

    # 메타데이터
    specs = Column(JSON)  # 장비 사양
    process_capabilities = Column(JSON)  # 처리 가능한 공정 목록

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wip_items = relationship("WIPItem", back_populates="equipment")


class WIPItem(Base):
    """Work In Progress 모델"""
    __tablename__ = "wip_items"

    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(String(50), unique=True, index=True, nullable=False)
    product_id = Column(String(50), nullable=False)

    # 웨이퍼 정보
    wafer_count = Column(Integer, nullable=False)

    # 공정 진행 상태
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, nullable=False)
    current_operation = Column(String(100))

    # 우선순위 및 일정
    priority = Column(Integer, default=5)  # 1-10, 10이 최고 우선순위
    due_date = Column(DateTime)
    estimated_completion = Column(DateTime)

    # 현재 위치
    current_bay = Column(String(50))
    current_queue = Column(String(50))  # 대기 중인 장비
    equipment_id = Column(Integer, ForeignKey("fab_equipment.id"))

    # 상태
    status = Column(String(20), default="QUEUED")  # QUEUED, PROCESSING, HOLD, COMPLETE
    hold_reason = Column(String(200))

    # 타임스탬프
    start_time = Column(DateTime)
    last_move_time = Column(DateTime, default=datetime.utcnow)

    # 메타데이터
    route = Column(JSON)  # 공정 라우트 [{step, operation, equipment_type}]
    history = Column(JSON)  # 이동 이력

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    equipment = relationship("FabEquipment", back_populates="wip_items")


class SimulationScenario(Base):
    """시뮬레이션 시나리오 모델"""
    __tablename__ = "simulation_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))

    # 시나리오 유형
    scenario_type = Column(String(50), nullable=False)  # EQUIPMENT_FAILURE, DEMAND_SPIKE, NEW_PROCESS, MAINTENANCE

    # 파라미터
    parameters = Column(JSON, nullable=False)
    """
    예시 파라미터:
    {
        "equipment_id": "LITHO-03",
        "failure_type": "UNPLANNED",
        "duration_hours": 24,
        "start_time": "2026-01-30T08:00:00"
    }
    """

    # 실행 상태
    status = Column(String(20), default="DRAFT")  # DRAFT, RUNNING, COMPLETED, FAILED

    # 결과
    baseline_metrics = Column(JSON)
    scenario_metrics = Column(JSON)
    impact_analysis = Column(JSON)
    recommendations = Column(JSON)
    confidence_score = Column(Float)

    # 메타데이터
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime)
    completed_at = Column(DateTime)


class Bottleneck(Base):
    """병목 예측 모델"""
    __tablename__ = "bottlenecks"

    id = Column(Integer, primary_key=True, index=True)
    bottleneck_id = Column(String(50), unique=True, index=True, nullable=False)

    # 대상
    equipment_id = Column(String(50), nullable=False)
    equipment_type = Column(String(50))
    bay = Column(String(50))

    # 예측 정보
    predicted_time = Column(DateTime, nullable=False)
    predicted_queue_length = Column(Integer)
    predicted_wait_hours = Column(Float)

    # 심각도
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float)  # 예측 신뢰도 0-100

    # 영향 분석
    affected_lots = Column(JSON)  # 영향받는 Lot ID 목록
    impact_description = Column(String(500))

    # 권장 조치
    recommended_actions = Column(JSON)

    # 상태
    status = Column(String(20), default="PREDICTED")  # PREDICTED, CONFIRMED, MITIGATED, FALSE_POSITIVE
    actual_occurrence = Column(DateTime)
    resolution_notes = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MaintenanceSchedule(Base):
    """유지보수 일정 모델"""
    __tablename__ = "maintenance_schedules"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(String(50), unique=True, index=True, nullable=False)

    equipment_id = Column(String(50), nullable=False)
    maintenance_type = Column(String(50), nullable=False)  # PM, CALIBRATION, REPAIR, UPGRADE

    # 일정
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)

    # 상태
    status = Column(String(20), default="SCHEDULED")  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED

    # 상세 정보
    description = Column(String(500))
    parts_required = Column(JSON)
    assigned_technician = Column(String(100))

    # 영향 분석
    estimated_downtime_hours = Column(Float)
    affected_capacity_wph = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
