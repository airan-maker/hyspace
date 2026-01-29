"""
Supply Chain Models

공급망 관리를 위한 데이터 모델
Tier-N 가시성, 리스크 관리, 재고 최적화
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class SupplierTier(str, enum.Enum):
    TIER_0 = "TIER_0"  # 자사
    TIER_1 = "TIER_1"  # 1차 협력사
    TIER_2 = "TIER_2"  # 2차 협력사
    TIER_3 = "TIER_3"  # 원자재 공급


class RiskSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskType(str, enum.Enum):
    GEOPOLITICAL = "GEOPOLITICAL"
    LOGISTICS = "LOGISTICS"
    QUALITY = "QUALITY"
    CAPACITY = "CAPACITY"
    FINANCIAL = "FINANCIAL"
    NATURAL_DISASTER = "NATURAL_DISASTER"


class MaterialCriticality(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Many-to-many relationship between Supplier and Material
supplier_materials = Table(
    'supplier_materials',
    Base.metadata,
    Column('supplier_id', Integer, ForeignKey('suppliers.id'), primary_key=True),
    Column('material_id', Integer, ForeignKey('materials.id'), primary_key=True)
)


class Supplier(Base):
    """공급업체 모델"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    tier = Column(String(20), nullable=False)  # TIER_1, TIER_2, TIER_3

    # 위치 정보
    country = Column(String(100))
    region = Column(String(100))
    address = Column(String(500))

    # 연락처
    contact_name = Column(String(100))
    contact_email = Column(String(200))
    contact_phone = Column(String(50))

    # 성능 지표
    lead_time_days = Column(Integer)  # 평균 리드타임
    on_time_delivery_rate = Column(Float)  # 정시 납품률 (%)
    quality_rating = Column(Float)  # 품질 평가 (0-100)
    risk_score = Column(Float)  # 리스크 점수 (0-100)

    # 지정학적 리스크
    geopolitical_exposure = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL

    # 계약 정보
    contract_start = Column(DateTime)
    contract_end = Column(DateTime)
    contract_status = Column(String(20))  # ACTIVE, EXPIRED, PENDING

    # 역량 정보
    annual_capacity = Column(Float)
    current_utilization = Column(Float)
    certifications = Column(JSON)  # ISO 인증 목록

    # 메타데이터
    notes = Column(String(1000))
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    materials = relationship("Material", secondary=supplier_materials, back_populates="suppliers")
    risks = relationship("SupplyRisk", back_populates="supplier")


class Material(Base):
    """자재 모델"""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # WAFER, GAS, CHEMICAL, EQUIPMENT, SPARE_PART

    # 재고 정보
    current_stock = Column(Float, default=0)
    unit = Column(String(20))  # EA, KG, L, etc.
    safety_stock = Column(Float)  # 안전 재고
    reorder_point = Column(Float)  # 재발주점
    max_stock = Column(Float)  # 최대 재고

    # 비용 정보
    unit_cost = Column(Float)
    currency = Column(String(10), default="USD")
    total_value = Column(Float)  # current_stock * unit_cost

    # 리드타임
    lead_time_days = Column(Integer)  # 평균 리드타임
    lead_time_min = Column(Integer)  # 최소 리드타임
    lead_time_max = Column(Integer)  # 최대 리드타임

    # 중요도
    criticality = Column(String(20))  # CRITICAL, HIGH, MEDIUM, LOW
    substitute_available = Column(Boolean, default=False)

    # 소비 정보
    daily_consumption = Column(Float)  # 일평균 소비량
    monthly_consumption = Column(Float)

    # 사양
    specifications = Column(JSON)

    # 메타데이터
    last_order_date = Column(DateTime)
    last_received_date = Column(DateTime)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    suppliers = relationship("Supplier", secondary=supplier_materials, back_populates="materials")
    risks = relationship("SupplyRisk", back_populates="material")
    recommendations = relationship("InventoryRecommendation", back_populates="material")


class SupplyRisk(Base):
    """공급 리스크 모델"""
    __tablename__ = "supply_risks"

    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(String(2000))

    # 리스크 분류
    risk_type = Column(String(50), nullable=False)  # GEOPOLITICAL, LOGISTICS, QUALITY, CAPACITY
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    probability = Column(Float)  # 발생 확률 (0-100)

    # 영향 범위
    affected_supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    affected_material_id = Column(Integer, ForeignKey("materials.id"))
    affected_products = Column(JSON)  # 영향받는 제품 목록

    # 영향 분석
    estimated_impact_days = Column(Integer)  # 예상 영향 기간
    estimated_cost_impact = Column(Float)  # 예상 비용 영향
    production_impact_percent = Column(Float)  # 생산 영향 (%)

    # 원인 및 출처
    source = Column(String(100))  # NEWS, SENSOR, SUPPLIER_REPORT, INTERNAL
    source_url = Column(String(500))
    detected_at = Column(DateTime, default=datetime.utcnow)

    # 대응
    status = Column(String(20), default="OPEN")  # OPEN, MONITORING, MITIGATING, RESOLVED
    mitigation_actions = Column(JSON)  # 완화 조치 목록
    assigned_to = Column(String(100))

    # 해결
    resolved_at = Column(DateTime)
    resolution_notes = Column(String(1000))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="risks")
    material = relationship("Material", back_populates="risks")


class InventoryRecommendation(Base):
    """재고 최적화 권장사항 모델"""
    __tablename__ = "inventory_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(String(50), unique=True, index=True, nullable=False)

    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)

    # 권장 행동
    action = Column(String(50), nullable=False)  # REORDER, EXPEDITE, REDUCE, REDISTRIBUTE
    urgency = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL

    # 상세 내용
    quantity = Column(Float)
    target_supplier_id = Column(String(50))
    rationale = Column(String(500))

    # 영향 분석
    cost_impact = Column(Float)  # 비용 영향 (절감 시 음수)
    risk_mitigation = Column(String(200))  # 리스크 완화 효과

    # 상태
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, EXECUTED, REJECTED
    approved_by = Column(String(100))
    executed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    material = relationship("Material", back_populates="recommendations")


class SupplyChainEvent(Base):
    """공급망 이벤트 로그 모델"""
    __tablename__ = "supply_chain_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, index=True, nullable=False)

    event_type = Column(String(50), nullable=False)  # ORDER, DELIVERY, SHORTAGE, PRICE_CHANGE
    description = Column(String(500))

    # 관련 엔티티
    supplier_id = Column(String(50))
    material_id = Column(String(50))

    # 상세 정보
    quantity = Column(Float)
    unit_price = Column(Float)
    total_value = Column(Float)

    # 타임스탬프
    event_time = Column(DateTime, default=datetime.utcnow)
    expected_delivery = Column(DateTime)
    actual_delivery = Column(DateTime)

    # 메타데이터
    reference_number = Column(String(100))  # PO number, etc.
    notes = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)
