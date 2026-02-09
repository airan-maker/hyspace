"""
Yield Schemas

수율 관련 Pydantic 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class YieldEventStatusEnum(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    ROOT_CAUSE_IDENTIFIED = "ROOT_CAUSE_IDENTIFIED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class SeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"
    CATASTROPHIC = "CATASTROPHIC"


class RootCauseTypeEnum(str, Enum):
    EQUIPMENT = "EQUIPMENT"
    MATERIAL = "MATERIAL"
    PROCESS = "PROCESS"
    HUMAN = "HUMAN"
    ENVIRONMENT = "ENVIRONMENT"
    UNKNOWN = "UNKNOWN"


# Wafer Record Schemas
class WaferRecordBase(BaseModel):
    wafer_id: str
    lot_id: str
    product_id: Optional[str] = None
    process_step: Optional[int] = None
    equipment_id: Optional[str] = None
    recipe_id: Optional[str] = None
    yield_percent: Optional[float] = None
    die_count: Optional[int] = None
    good_die_count: Optional[int] = None
    defect_count: Optional[int] = None


class WaferRecordCreate(WaferRecordBase):
    sensor_data: Optional[dict] = None
    metrology_data: Optional[dict] = None
    defect_map: Optional[list] = None


class WaferRecordResponse(WaferRecordBase):
    id: int
    sensor_data: Optional[dict] = None
    metrology_data: Optional[dict] = None
    defect_map: Optional[list] = None
    process_start: Optional[datetime] = None
    process_end: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Root Cause Schema
class RootCause(BaseModel):
    model_config = {"populate_by_name": True}

    cause_type: RootCauseTypeEnum = Field(alias="type")
    entity_id: str = Field(..., description="관련 엔티티 ID (장비ID, 재료 배치ID 등)")
    description: str
    probability: float = Field(..., ge=0, le=100, description="원인일 확률 (%)")
    evidence: list[str] = Field(default_factory=list, description="근거 데이터")


# Yield Event Schemas
class YieldEventBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    severity: SeverityEnum = SeverityEnum.MEDIUM


class YieldEventCreate(YieldEventBase):
    yield_drop_percent: float = Field(..., ge=0, le=100)
    affected_wafer_ids: Optional[list[str]] = None
    affected_lot_ids: Optional[list[str]] = None
    process_step: Optional[int] = None
    equipment_ids: Optional[list[str]] = None
    product_ids: Optional[list[str]] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None


class YieldEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[YieldEventStatusEnum] = None
    severity: Optional[SeverityEnum] = None
    assigned_to: Optional[str] = None
    analysis_summary: Optional[str] = None
    recommendations: Optional[list[str]] = None


class YieldEventResponse(YieldEventBase):
    id: int
    event_id: str
    status: YieldEventStatusEnum
    yield_drop_percent: float
    affected_wafer_count: Optional[int] = None
    affected_lot_ids: Optional[list[str]] = None

    root_causes: Optional[list[RootCause]] = None
    analysis_summary: Optional[str] = None
    recommendations: Optional[list[str]] = None

    detected_at: datetime
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


# Root Cause Analysis Schemas
class RCARequest(BaseModel):
    """Root Cause Analysis 요청"""
    event_id: str
    analysis_depth: int = Field(default=3, ge=1, le=5, description="분석 깊이")
    include_similar_events: bool = Field(default=True)
    time_window_hours: int = Field(default=48, description="분석 시간 범위")


class RCAResponse(BaseModel):
    """Root Cause Analysis 결과"""
    event_id: str
    root_causes: list[RootCause]
    confidence_score: float = Field(..., ge=0, le=100)
    similar_events: Optional[list[str]] = None
    analysis_method: str
    recommendations: list[str]
    analysis_time_seconds: float


# Yield Dashboard Schemas
class YieldTrendPoint(BaseModel):
    date: datetime
    yield_percent: float
    wafer_count: int


class YieldByEquipment(BaseModel):
    equipment_id: str
    equipment_type: str
    avg_yield: float
    wafer_count: int
    trend: str  # UP, DOWN, STABLE


class YieldByProduct(BaseModel):
    product_id: str
    avg_yield: float
    wafer_count: int


class YieldDashboardResponse(BaseModel):
    """수율 대시보드 데이터"""
    overall_yield: float
    yield_target: float
    yield_vs_target: float  # +/- percent

    trend_data: list[YieldTrendPoint]
    by_equipment: list[YieldByEquipment]
    by_product: list[YieldByProduct]

    active_events: int
    critical_events: int
    events_this_week: int

    top_defect_types: list[dict]
    recent_alerts: list[dict]


# Equipment Schemas
class EquipmentBase(BaseModel):
    equipment_id: str
    equipment_type: str
    bay: Optional[str] = None


class EquipmentResponse(EquipmentBase):
    id: int
    capacity_wph: Optional[float] = None
    oee: Optional[float] = None
    mtbf_hours: Optional[float] = None
    mttr_hours: Optional[float] = None
    status: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None

    class Config:
        from_attributes = True
