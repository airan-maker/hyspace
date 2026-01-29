"""
Yield API Endpoints

수율 관리 및 근본 원인 분석 API
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.yield_analyzer import YieldAnalyzer
from app.services.audit_logger import AuditLogger
from app.services.data_masking import DataMaskingService
from app.schemas.yield_schema import (
    WaferRecordCreate, WaferRecordResponse,
    YieldEventCreate, YieldEventUpdate, YieldEventResponse,
    RCARequest, RCAResponse,
    YieldDashboardResponse,
    YieldTrendPoint, YieldByEquipment, YieldByProduct,
    EquipmentResponse,
)
from app.models.yield_event import WaferRecord, YieldEvent, Equipment

router = APIRouter(prefix="/yield", tags=["Yield Management"])


# ==================== Wafer Records ====================

@router.post("/wafers", response_model=WaferRecordResponse)
def create_wafer_record(
    wafer: WaferRecordCreate,
    db: Session = Depends(get_db)
):
    """웨이퍼 레코드 생성"""
    db_wafer = WaferRecord(
        wafer_id=wafer.wafer_id,
        lot_id=wafer.lot_id,
        product_id=wafer.product_id,
        process_step=wafer.process_step,
        equipment_id=wafer.equipment_id,
        recipe_id=wafer.recipe_id,
        yield_percent=wafer.yield_percent,
        die_count=wafer.die_count,
        good_die_count=wafer.good_die_count,
        defect_count=wafer.defect_count,
        sensor_data=wafer.sensor_data,
        metrology_data=wafer.metrology_data,
        defect_map=wafer.defect_map,
    )

    db.add(db_wafer)
    db.commit()
    db.refresh(db_wafer)

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,  # TODO: 실제 사용자 ID
        user_role="system",
        action="CREATE",
        resource="wafer_record",
        resource_id=db_wafer.wafer_id,
        details={"lot_id": db_wafer.lot_id}
    )

    return db_wafer


@router.get("/wafers", response_model=list[WaferRecordResponse])
def get_wafer_records(
    lot_id: Optional[str] = None,
    equipment_id: Optional[str] = None,
    product_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """웨이퍼 레코드 목록 조회"""
    query = db.query(WaferRecord)

    if lot_id:
        query = query.filter(WaferRecord.lot_id == lot_id)
    if equipment_id:
        query = query.filter(WaferRecord.equipment_id == equipment_id)
    if product_id:
        query = query.filter(WaferRecord.product_id == product_id)

    return query.offset(skip).limit(limit).all()


@router.get("/wafers/{wafer_id}", response_model=WaferRecordResponse)
def get_wafer_record(
    wafer_id: str,
    db: Session = Depends(get_db)
):
    """특정 웨이퍼 레코드 조회"""
    wafer = db.query(WaferRecord).filter(WaferRecord.wafer_id == wafer_id).first()
    if not wafer:
        raise HTTPException(status_code=404, detail="Wafer record not found")
    return wafer


# ==================== Yield Events ====================

@router.post("/events", response_model=YieldEventResponse)
def create_yield_event(
    event: YieldEventCreate,
    db: Session = Depends(get_db)
):
    """수율 이벤트 생성"""
    analyzer = YieldAnalyzer(db)
    db_event = analyzer.create_yield_event(event, created_by="system")

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="CREATE",
        resource="yield_event",
        resource_id=db_event.event_id,
        details={"severity": event.severity.value, "yield_drop": event.yield_drop_percent}
    )

    return db_event


@router.get("/events", response_model=list[YieldEventResponse])
def get_yield_events(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """수율 이벤트 목록 조회"""
    analyzer = YieldAnalyzer(db)
    events = analyzer.get_yield_events(
        status=status,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return events


@router.get("/events/{event_id}", response_model=YieldEventResponse)
def get_yield_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """특정 수율 이벤트 조회"""
    event = db.query(YieldEvent).filter(YieldEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Yield event not found")
    return event


@router.put("/events/{event_id}", response_model=YieldEventResponse)
def update_yield_event(
    event_id: str,
    update: YieldEventUpdate,
    db: Session = Depends(get_db)
):
    """수율 이벤트 업데이트"""
    event = db.query(YieldEvent).filter(YieldEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Yield event not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if hasattr(value, 'value'):  # Enum 처리
                setattr(event, field, value.value)
            else:
                setattr(event, field, value)

    # 상태가 RESOLVED로 변경되면 resolved_at 설정
    if update.status and update.status.value == "RESOLVED":
        event.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(event)

    # 감사 로그
    audit = AuditLogger(db)
    audit.log_edit(
        user_id=0,
        user_role="system",
        resource="yield_event",
        resource_id=event_id,
        new_value=update_data
    )

    return event


# ==================== Root Cause Analysis ====================

@router.post("/analyze/{event_id}", response_model=RCAResponse)
def analyze_root_cause(
    event_id: str,
    analysis_depth: int = Query(default=3, ge=1, le=5),
    include_similar: bool = True,
    time_window_hours: int = Query(default=48, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    근본 원인 분석 실행

    - event_id: 분석할 수율 이벤트 ID
    - analysis_depth: 분석 깊이 (1-5, 기본값 3)
    - include_similar: 유사 이벤트 포함 여부
    - time_window_hours: 분석 시간 범위 (시간)
    """
    # 이벤트 존재 확인
    event = db.query(YieldEvent).filter(YieldEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Yield event not found")

    analyzer = YieldAnalyzer(db)

    request = RCARequest(
        event_id=event_id,
        analysis_depth=analysis_depth,
        include_similar_events=include_similar,
        time_window_hours=time_window_hours
    )

    result = analyzer.analyze_root_cause(request)

    # 이벤트 상태 업데이트
    if event.status == "OPEN":
        event.status = "INVESTIGATING"
        db.commit()

    # 분석 결과 저장
    if result.root_causes:
        event.root_causes = [
            {
                "cause_type": rc.cause_type.value,
                "entity_id": rc.entity_id,
                "description": rc.description,
                "probability": rc.probability,
                "evidence": rc.evidence
            }
            for rc in result.root_causes
        ]
        event.analysis_summary = f"분석 완료: {len(result.root_causes)}개 원인 식별 (신뢰도 {result.confidence_score:.1f}%)"
        event.recommendations = result.recommendations
        db.commit()

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="ANALYZE",
        resource="yield_event",
        resource_id=event_id,
        details={
            "analysis_depth": analysis_depth,
            "causes_found": len(result.root_causes),
            "confidence": result.confidence_score
        }
    )

    return result


# ==================== Dashboard ====================

@router.get("/dashboard", response_model=YieldDashboardResponse)
def get_yield_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    product_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    수율 대시보드 데이터 조회

    - days: 조회 기간 (일)
    - product_id: 특정 제품 필터 (선택)
    """
    analyzer = YieldAnalyzer(db)
    return analyzer.get_dashboard_data(days=days, product_id=product_id)


@router.get("/trends", response_model=list[YieldTrendPoint])
def get_yield_trends(
    days: int = Query(default=30, ge=1, le=365),
    product_id: Optional[str] = None,
    equipment_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    수율 트렌드 데이터 조회

    일별 수율 추이 데이터 반환
    """
    analyzer = YieldAnalyzer(db)
    dashboard = analyzer.get_dashboard_data(days=days, product_id=product_id)
    return dashboard.trend_data


@router.get("/by-equipment", response_model=list[YieldByEquipment])
def get_yield_by_equipment(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """장비별 수율 데이터"""
    analyzer = YieldAnalyzer(db)
    dashboard = analyzer.get_dashboard_data(days=days)
    return dashboard.by_equipment


@router.get("/by-product", response_model=list[YieldByProduct])
def get_yield_by_product(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """제품별 수율 데이터"""
    analyzer = YieldAnalyzer(db)
    dashboard = analyzer.get_dashboard_data(days=days)
    return dashboard.by_product


# ==================== Equipment ====================

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
    query = db.query(Equipment)

    if equipment_type:
        query = query.filter(Equipment.equipment_type == equipment_type)
    if bay:
        query = query.filter(Equipment.bay == bay)
    if status:
        query = query.filter(Equipment.status == status)

    return query.offset(skip).limit(limit).all()


@router.get("/equipment/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """특정 장비 조회"""
    equipment = db.query(Equipment).filter(Equipment.equipment_id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


# ==================== Statistics ====================

@router.get("/statistics")
def get_yield_statistics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    수율 통계 요약

    Returns:
        전체 수율, 이벤트 수, 주요 지표 등
    """
    analyzer = YieldAnalyzer(db)
    dashboard = analyzer.get_dashboard_data(days=days)

    return {
        "period_days": days,
        "overall_yield": dashboard.overall_yield,
        "yield_target": dashboard.yield_target,
        "yield_vs_target": dashboard.yield_vs_target,
        "active_events": dashboard.active_events,
        "critical_events": dashboard.critical_events,
        "events_this_week": dashboard.events_this_week,
        "top_defect_types": dashboard.top_defect_types,
        "equipment_count": len(dashboard.by_equipment),
        "product_count": len(dashboard.by_product)
    }
