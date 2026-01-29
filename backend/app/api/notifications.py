"""
Notification API Endpoints

알림 관리 API
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.notification import NotificationService
from app.services.audit_logger import AuditLogger
from app.models.notification import AlertRule, Alert, NotificationRecipient

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ==================== Schemas ====================

class AlertRuleCreate(BaseModel):
    name: str
    metric: str
    rule_type: str = Field(..., description="THRESHOLD, ANOMALY, TREND, EVENT")
    severity: str = Field(..., description="INFO, WARNING, ERROR, CRITICAL")
    operator: str = "<"
    threshold_value: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    cooldown_minutes: int = 30
    escalation_enabled: bool = False


class AlertRuleResponse(BaseModel):
    id: int
    rule_id: str
    name: str
    metric: str
    rule_type: str
    severity: str
    operator: Optional[str]
    threshold_value: Optional[float]
    category: Optional[str]
    description: Optional[str]
    is_active: bool
    is_muted: bool
    last_triggered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    threshold_value: Optional[float] = None
    severity: Optional[str] = None
    is_active: Optional[bool] = None
    cooldown_minutes: Optional[int] = None


class AlertResponse(BaseModel):
    id: int
    alert_id: str
    title: str
    message: Optional[str]
    severity: str
    metric_name: Optional[str]
    metric_value: Optional[float]
    threshold_value: Optional[float]
    entity_type: Optional[str]
    entity_id: Optional[str]
    status: str
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    triggered_at: datetime

    class Config:
        from_attributes = True


class RecipientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    slack_user_id: Optional[str] = None
    role: Optional[str] = None
    preferred_channels: list[str] = ["IN_APP"]
    escalation_level: int = 1


class RecipientResponse(BaseModel):
    id: int
    recipient_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    role: Optional[str]
    preferred_channels: Optional[list]
    escalation_level: int
    is_active: bool

    class Config:
        from_attributes = True


class MetricsCheck(BaseModel):
    metrics: dict[str, float]


class AlertAcknowledge(BaseModel):
    acknowledged_by: str


class AlertResolve(BaseModel):
    resolved_by: str
    resolution_notes: Optional[str] = None


# ==================== Alert Rules ====================

@router.post("/rules", response_model=AlertRuleResponse)
def create_alert_rule(
    rule: AlertRuleCreate,
    db: Session = Depends(get_db)
):
    """알림 규칙 생성"""
    service = NotificationService(db)

    db_rule = service.create_rule(
        name=rule.name,
        metric=rule.metric,
        rule_type=rule.rule_type,
        severity=rule.severity,
        operator=rule.operator,
        threshold_value=rule.threshold_value,
        category=rule.category,
        description=rule.description,
        cooldown_minutes=rule.cooldown_minutes,
        escalation_enabled=rule.escalation_enabled
    )

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="CREATE",
        resource="alert_rule",
        resource_id=db_rule.rule_id
    )

    return db_rule


@router.get("/rules", response_model=list[AlertRuleResponse])
def get_alert_rules(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """알림 규칙 목록 조회"""
    service = NotificationService(db)
    return service.get_rules(category=category, is_active=is_active, limit=limit)


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
def get_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db)
):
    """특정 알림 규칙 조회"""
    rule = db.query(AlertRule).filter(AlertRule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
def update_alert_rule(
    rule_id: str,
    update: AlertRuleUpdate,
    db: Session = Depends(get_db)
):
    """알림 규칙 업데이트"""
    service = NotificationService(db)

    try:
        updated = service.update_rule(rule_id, **update.model_dump(exclude_unset=True))
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rules/{rule_id}/mute")
def mute_alert_rule(
    rule_id: str,
    duration_minutes: int = Query(default=60, ge=1, le=1440),
    db: Session = Depends(get_db)
):
    """알림 규칙 일시 음소거"""
    service = NotificationService(db)

    try:
        rule = service.mute_rule(rule_id, duration_minutes)
        return {
            "message": f"Rule {rule_id} muted for {duration_minutes} minutes",
            "mute_until": rule.mute_until.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rules/{rule_id}/unmute")
def unmute_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db)
):
    """알림 규칙 음소거 해제"""
    rule = db.query(AlertRule).filter(AlertRule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    rule.is_muted = False
    rule.mute_until = None
    db.commit()

    return {"message": f"Rule {rule_id} unmuted"}


# ==================== Alerts ====================

@router.get("/alerts", response_model=list[AlertResponse])
def get_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """알림 목록 조회"""
    service = NotificationService(db)
    return service.get_alerts(
        status=status,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


@router.get("/alerts/summary")
def get_alert_summary(
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """알림 요약 통계"""
    service = NotificationService(db)
    return service.get_alert_summary(hours=hours)


@router.get("/alerts/active", response_model=list[AlertResponse])
def get_active_alerts(
    db: Session = Depends(get_db)
):
    """활성 알림 목록"""
    service = NotificationService(db)
    return service.get_alerts(status="ACTIVE", limit=50)


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """특정 알림 조회"""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: str,
    data: AlertAcknowledge,
    db: Session = Depends(get_db)
):
    """알림 확인"""
    service = NotificationService(db)

    try:
        alert = service.acknowledge_alert(alert_id, data.acknowledged_by)

        # 감사 로그
        audit = AuditLogger(db)
        audit.log(
            user_id=0,
            user_role="system",
            action="ACKNOWLEDGE",
            resource="alert",
            resource_id=alert_id,
            details={"acknowledged_by": data.acknowledged_by}
        )

        return alert
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: str,
    data: AlertResolve,
    db: Session = Depends(get_db)
):
    """알림 해결"""
    service = NotificationService(db)

    try:
        alert = service.resolve_alert(
            alert_id,
            data.resolved_by,
            data.resolution_notes
        )

        # 감사 로그
        audit = AuditLogger(db)
        audit.log(
            user_id=0,
            user_role="system",
            action="RESOLVE",
            resource="alert",
            resource_id=alert_id,
            details={"resolved_by": data.resolved_by}
        )

        return alert
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== Recipients ====================

@router.post("/recipients", response_model=RecipientResponse)
def create_recipient(
    recipient: RecipientCreate,
    db: Session = Depends(get_db)
):
    """알림 수신자 등록"""
    service = NotificationService(db)

    db_recipient = service.create_recipient(
        name=recipient.name,
        email=recipient.email,
        phone=recipient.phone,
        slack_user_id=recipient.slack_user_id,
        role=recipient.role,
        preferred_channels=recipient.preferred_channels,
        escalation_level=recipient.escalation_level
    )

    return db_recipient


@router.get("/recipients", response_model=list[RecipientResponse])
def get_recipients(
    escalation_level: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """알림 수신자 목록"""
    service = NotificationService(db)
    return service.get_recipients(escalation_level=escalation_level)


@router.get("/recipients/{recipient_id}", response_model=RecipientResponse)
def get_recipient(
    recipient_id: str,
    db: Session = Depends(get_db)
):
    """특정 수신자 조회"""
    recipient = db.query(NotificationRecipient).filter(
        NotificationRecipient.recipient_id == recipient_id
    ).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    return recipient


# ==================== Real-time Check ====================

@router.post("/check")
def check_metrics_and_alert(
    data: MetricsCheck,
    db: Session = Depends(get_db)
):
    """
    메트릭 체크 및 알림 발송

    실시간 모니터링 시스템에서 주기적으로 호출
    """
    service = NotificationService(db)
    alerts = service.check_and_alert(data.metrics)

    return {
        "checked_at": datetime.utcnow().isoformat(),
        "metrics_checked": len(data.metrics),
        "alerts_triggered": len(alerts),
        "alerts": [
            {"alert_id": a.alert_id, "title": a.title, "severity": a.severity}
            for a in alerts
        ]
    }


# ==================== Demo Data ====================

@router.post("/demo/generate-alerts")
def generate_demo_alerts(
    count: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """데모 알림 생성"""
    import random

    service = NotificationService(db)

    demo_metrics = [
        ("overall_yield", 75.0 + random.uniform(0, 20)),
        ("equipment_oee", 70.0 + random.uniform(0, 20)),
        ("inventory_level", 10.0 + random.uniform(0, 30)),
        ("supply_risk_score", 50.0 + random.uniform(0, 40)),
    ]

    generated = []
    for _ in range(count):
        metric, value = random.choice(demo_metrics)
        alerts = service.check_and_alert({metric: value})
        generated.extend(alerts)

    return {
        "generated_count": len(generated),
        "alerts": [
            {"alert_id": a.alert_id, "title": a.title, "severity": a.severity}
            for a in generated
        ]
    }
