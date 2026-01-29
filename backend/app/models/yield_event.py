"""
Yield Event Models

수율 이벤트 및 웨이퍼 데이터 모델
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class YieldEventStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    ROOT_CAUSE_IDENTIFIED = "ROOT_CAUSE_IDENTIFIED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class RootCauseType(str, enum.Enum):
    EQUIPMENT = "EQUIPMENT"
    MATERIAL = "MATERIAL"
    PROCESS = "PROCESS"
    HUMAN = "HUMAN"
    ENVIRONMENT = "ENVIRONMENT"
    UNKNOWN = "UNKNOWN"


class WaferRecord(Base):
    """웨이퍼 레코드"""
    __tablename__ = "wafer_records"

    id = Column(Integer, primary_key=True, index=True)
    wafer_id = Column(String(50), unique=True, index=True, nullable=False)
    lot_id = Column(String(50), index=True, nullable=False)
    product_id = Column(String(50), index=True)
    process_step = Column(Integer)
    equipment_id = Column(String(50), index=True)
    recipe_id = Column(String(50))

    # 측정 데이터
    yield_percent = Column(Float)
    die_count = Column(Integer)
    good_die_count = Column(Integer)
    defect_count = Column(Integer)

    # 센서 데이터 (JSON)
    sensor_data = Column(JSON)  # {temp, pressure, flow, etc.}
    metrology_data = Column(JSON)  # {cd, overlay, thickness, etc.}
    defect_map = Column(JSON)  # [{x, y, type, size}, ...]

    # 타임스탬프
    process_start = Column(DateTime)
    process_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    yield_events = relationship("YieldEventWafer", back_populates="wafer")


class YieldEvent(Base):
    """수율 이벤트 (수율 저하 발생 시 생성)"""
    __tablename__ = "yield_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, index=True, nullable=False)

    # 이벤트 정보
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    status = Column(Enum(YieldEventStatus), default=YieldEventStatus.OPEN)
    severity = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL

    # 수율 영향
    yield_drop_percent = Column(Float)
    affected_wafer_count = Column(Integer)
    affected_lot_ids = Column(JSON)  # ["LOT001", "LOT002", ...]

    # 필터 조건
    process_step = Column(Integer)
    equipment_ids = Column(JSON)
    product_ids = Column(JSON)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)

    # 분석 결과
    root_causes = Column(JSON)  # [{type, entity_id, probability, evidence}, ...]
    analysis_summary = Column(String(2000))
    recommendations = Column(JSON)

    # 타임스탬프
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 담당자
    assigned_to = Column(String(100))
    created_by = Column(String(100))

    # 관계
    wafers = relationship("YieldEventWafer", back_populates="event")


class YieldEventWafer(Base):
    """수율 이벤트 - 웨이퍼 연결 테이블"""
    __tablename__ = "yield_event_wafers"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("yield_events.id"))
    wafer_id = Column(Integer, ForeignKey("wafer_records.id"))

    event = relationship("YieldEvent", back_populates="wafers")
    wafer = relationship("WaferRecord", back_populates="yield_events")


class Equipment(Base):
    """장비 정보"""
    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String(50), unique=True, index=True, nullable=False)
    equipment_type = Column(String(50))  # LITHO, ETCH, CVD, PVD, CMP
    bay = Column(String(20))

    # 성능 지표
    capacity_wph = Column(Float)  # Wafers Per Hour
    oee = Column(Float)  # Overall Equipment Effectiveness
    mtbf_hours = Column(Float)  # Mean Time Between Failures
    mttr_hours = Column(Float)  # Mean Time To Repair

    # 상태
    status = Column(String(20))  # RUNNING, IDLE, MAINTENANCE, DOWN
    last_maintenance = Column(DateTime)
    next_maintenance = Column(DateTime)

    # 메타데이터
    vendor = Column(String(100))
    model = Column(String(100))
    install_date = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
