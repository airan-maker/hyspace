"""
Supply Chain API Endpoints

공급망 관리 API
Tier-N 가시성, 리스크 관리, 재고 최적화
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.supply_chain import (
    SupplyChainService, RiskDetector, InventoryOptimizer, SupplyChainAnalytics
)
from app.services.audit_logger import AuditLogger
from app.models.supply_chain import Supplier, Material, SupplyRisk, InventoryRecommendation

router = APIRouter(prefix="/supply", tags=["Supply Chain"])


# ==================== Schemas ====================

class SupplierCreate(BaseModel):
    supplier_id: str
    name: str
    tier: str = Field(..., description="TIER_1, TIER_2, TIER_3")
    country: str
    region: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    lead_time_days: Optional[int] = None
    quality_rating: Optional[float] = None
    geopolitical_exposure: Optional[str] = None


class SupplierResponse(BaseModel):
    id: int
    supplier_id: str
    name: str
    tier: str
    country: str
    region: Optional[str]
    lead_time_days: Optional[int]
    on_time_delivery_rate: Optional[float]
    quality_rating: Optional[float]
    risk_score: Optional[float]
    geopolitical_exposure: Optional[str]
    contract_status: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class MaterialCreate(BaseModel):
    material_id: str
    name: str
    category: str = Field(..., description="WAFER, GAS, CHEMICAL, EQUIPMENT, SPARE_PART")
    unit: str
    current_stock: float = 0
    safety_stock: Optional[float] = None
    reorder_point: Optional[float] = None
    max_stock: Optional[float] = None
    unit_cost: Optional[float] = None
    lead_time_days: Optional[int] = None
    criticality: Optional[str] = None
    daily_consumption: Optional[float] = None


class MaterialResponse(BaseModel):
    id: int
    material_id: str
    name: str
    category: str
    unit: Optional[str]
    current_stock: Optional[float]
    safety_stock: Optional[float]
    reorder_point: Optional[float]
    unit_cost: Optional[float]
    lead_time_days: Optional[int]
    criticality: Optional[str]
    daily_consumption: Optional[float]
    total_value: Optional[float]
    is_active: bool

    class Config:
        from_attributes = True


class RiskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    risk_type: str = Field(..., description="GEOPOLITICAL, LOGISTICS, QUALITY, CAPACITY, FINANCIAL, NATURAL_DISASTER")
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    probability: Optional[float] = None
    source: str = "INTERNAL"
    affected_supplier_id: Optional[int] = None
    affected_material_id: Optional[int] = None


class RiskResponse(BaseModel):
    id: int
    risk_id: str
    title: str
    description: Optional[str]
    risk_type: str
    severity: str
    probability: Optional[float]
    source: Optional[str]
    status: str
    detected_at: datetime
    mitigation_actions: Optional[list]

    class Config:
        from_attributes = True


class OrderSimulationRequest(BaseModel):
    material_id: str
    order_quantity: float
    lead_time_days: int


# ==================== Dashboard ====================

@router.get("/dashboard")
def get_supply_chain_dashboard(db: Session = Depends(get_db)):
    """
    공급망 대시보드

    전체 공급망 현황, 리스크, 재고 상태 요약
    """
    analytics = SupplyChainAnalytics(db)
    return analytics.get_dashboard_data()


# ==================== Suppliers ====================

@router.post("/suppliers", response_model=SupplierResponse)
def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db)
):
    """공급업체 등록"""
    service = SupplyChainService(db)

    db_supplier = service.create_supplier(
        supplier_id=supplier.supplier_id,
        name=supplier.name,
        tier=supplier.tier,
        country=supplier.country,
        region=supplier.region,
        contact_name=supplier.contact_name,
        contact_email=supplier.contact_email,
        lead_time_days=supplier.lead_time_days,
        quality_rating=supplier.quality_rating,
        geopolitical_exposure=supplier.geopolitical_exposure
    )

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="CREATE",
        resource="supplier",
        resource_id=db_supplier.supplier_id
    )

    return db_supplier


@router.get("/suppliers", response_model=list[SupplierResponse])
def get_suppliers(
    tier: Optional[str] = None,
    country: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """공급업체 목록 조회"""
    service = SupplyChainService(db)
    return service.get_suppliers(tier=tier, country=country, limit=limit)


@router.get("/suppliers/hierarchy")
def get_supplier_hierarchy(db: Session = Depends(get_db)):
    """
    공급업체 계층 구조

    Tier별 공급업체 구조화된 목록
    """
    service = SupplyChainService(db)
    return service.get_supplier_hierarchy()


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: str,
    db: Session = Depends(get_db)
):
    """특정 공급업체 조회"""
    supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


# ==================== Materials ====================

@router.post("/materials", response_model=MaterialResponse)
def create_material(
    material: MaterialCreate,
    db: Session = Depends(get_db)
):
    """자재 등록"""
    service = SupplyChainService(db)

    db_material = service.create_material(
        material_id=material.material_id,
        name=material.name,
        category=material.category,
        unit=material.unit,
        current_stock=material.current_stock,
        safety_stock=material.safety_stock,
        reorder_point=material.reorder_point,
        max_stock=material.max_stock,
        unit_cost=material.unit_cost,
        lead_time_days=material.lead_time_days,
        criticality=material.criticality,
        daily_consumption=material.daily_consumption
    )

    # 총 가치 계산
    if db_material.current_stock and db_material.unit_cost:
        db_material.total_value = db_material.current_stock * db_material.unit_cost
        db.commit()

    return db_material


@router.get("/materials", response_model=list[MaterialResponse])
def get_materials(
    category: Optional[str] = None,
    criticality: Optional[str] = None,
    below_reorder: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """자재 목록 조회"""
    service = SupplyChainService(db)
    return service.get_materials(
        category=category,
        criticality=criticality,
        below_reorder=below_reorder,
        limit=limit
    )


@router.get("/materials/status")
def get_inventory_status(db: Session = Depends(get_db)):
    """재고 현황 요약"""
    service = SupplyChainService(db)
    return service.get_inventory_status()


@router.get("/materials/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: str,
    db: Session = Depends(get_db)
):
    """특정 자재 조회"""
    material = db.query(Material).filter(Material.material_id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


# ==================== Risks ====================

@router.post("/risks", response_model=RiskResponse)
def create_risk(
    risk: RiskCreate,
    db: Session = Depends(get_db)
):
    """리스크 수동 등록"""
    service = SupplyChainService(db)

    db_risk = service.create_risk(
        title=risk.title,
        description=risk.description,
        risk_type=risk.risk_type,
        severity=risk.severity,
        probability=risk.probability,
        source=risk.source,
        affected_supplier_id=risk.affected_supplier_id,
        affected_material_id=risk.affected_material_id
    )

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="CREATE",
        resource="supply_risk",
        resource_id=db_risk.risk_id,
        details={"severity": risk.severity, "type": risk.risk_type}
    )

    return db_risk


@router.get("/risks", response_model=list[RiskResponse])
def get_risks(
    severity: Optional[str] = None,
    risk_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """리스크 목록 조회"""
    service = SupplyChainService(db)
    return service.get_risks(
        severity=severity,
        risk_type=risk_type,
        status=status,
        limit=limit
    )


@router.get("/risks/scan")
def scan_risks(db: Session = Depends(get_db)):
    """
    리스크 자동 스캔

    재고 부족, 공급업체 집중, 리드타임 등 리스크 자동 탐지
    """
    detector = RiskDetector(db)
    detected = detector.scan_for_risks()

    return {
        "scan_time": datetime.utcnow().isoformat(),
        "total_detected": len(detected),
        "risks": detected
    }


@router.get("/risks/summary")
def get_risk_summary(db: Session = Depends(get_db)):
    """리스크 현황 요약"""
    service = SupplyChainService(db)
    return service.get_risk_summary()


@router.get("/risks/{risk_id}", response_model=RiskResponse)
def get_risk(
    risk_id: str,
    db: Session = Depends(get_db)
):
    """특정 리스크 조회"""
    risk = db.query(SupplyRisk).filter(SupplyRisk.risk_id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return risk


@router.put("/risks/{risk_id}/status")
def update_risk_status(
    risk_id: str,
    status: str = Query(..., description="OPEN, MONITORING, MITIGATING, RESOLVED"),
    resolution_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """리스크 상태 업데이트"""
    risk = db.query(SupplyRisk).filter(SupplyRisk.risk_id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    risk.status = status
    if status == "RESOLVED":
        risk.resolved_at = datetime.utcnow()
    if resolution_notes:
        risk.resolution_notes = resolution_notes

    db.commit()

    return {"message": f"Risk {risk_id} status updated to {status}"}


# ==================== Recommendations ====================

@router.get("/recommendations")
def get_recommendations(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    재고 최적화 권장사항

    AI 기반 재발주, 재고 조정 권장사항
    """
    optimizer = InventoryOptimizer(db)
    recommendations = optimizer.generate_recommendations()

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_recommendations": len(recommendations),
        "recommendations": recommendations[:limit]
    }


@router.post("/simulate/order")
def simulate_order(
    request: OrderSimulationRequest,
    db: Session = Depends(get_db)
):
    """
    발주 영향 시뮬레이션

    특정 자재 발주 시 예상 재고 변화 및 위험 분석
    """
    optimizer = InventoryOptimizer(db)

    try:
        result = optimizer.simulate_order_impact(
            material_id=request.material_id,
            order_quantity=request.order_quantity,
            lead_time_days=request.lead_time_days
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
