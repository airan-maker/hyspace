"""
Notification Service

알림 규칙 평가 및 알림 발송 서비스
"""

from datetime import datetime, timedelta
from typing import Optional, Any
import uuid
import json
import asyncio
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.notification import (
    AlertRule, Alert, NotificationChannelConfig,
    NotificationRecipient, NotificationLog
)


@dataclass
class AlertContext:
    """알림 컨텍스트"""
    metric_name: str
    metric_value: float
    threshold_value: Optional[float] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    additional_data: dict = None


class AlertRuleEngine:
    """알림 규칙 평가 엔진"""

    def __init__(self, db: Session):
        self.db = db

    def evaluate_all_rules(self, metrics: dict[str, float]) -> list[Alert]:
        """
        모든 활성 규칙 평가

        Args:
            metrics: 메트릭 이름-값 딕셔너리

        Returns:
            트리거된 알림 목록
        """
        triggered_alerts = []

        rules = self.db.query(AlertRule).filter(
            AlertRule.is_active == True,
            AlertRule.is_muted == False
        ).all()

        for rule in rules:
            if rule.metric in metrics:
                alert = self.evaluate_rule(rule, metrics[rule.metric])
                if alert:
                    triggered_alerts.append(alert)

        return triggered_alerts

    def evaluate_rule(
        self,
        rule: AlertRule,
        current_value: float,
        context: Optional[AlertContext] = None
    ) -> Optional[Alert]:
        """
        단일 규칙 평가

        Args:
            rule: 알림 규칙
            current_value: 현재 메트릭 값
            context: 추가 컨텍스트

        Returns:
            트리거되면 Alert, 아니면 None
        """
        # 쿨다운 체크
        if not self._check_cooldown(rule):
            return None

        # 규칙 유형별 평가
        triggered = False

        if rule.rule_type == "THRESHOLD":
            triggered = self._evaluate_threshold(rule, current_value)
        elif rule.rule_type == "ANOMALY":
            triggered = self._evaluate_anomaly(rule, current_value)
        elif rule.rule_type == "TREND":
            triggered = self._evaluate_trend(rule, current_value)

        if triggered:
            return self._create_alert(rule, current_value, context)

        return None

    def _check_cooldown(self, rule: AlertRule) -> bool:
        """쿨다운 체크"""
        if not rule.last_triggered_at:
            return True

        cooldown_end = rule.last_triggered_at + timedelta(minutes=rule.cooldown_minutes or 30)
        return datetime.utcnow() > cooldown_end

    def _evaluate_threshold(self, rule: AlertRule, value: float) -> bool:
        """임계값 기반 평가"""
        if not rule.threshold_value:
            return False

        operator = rule.operator or "<"
        threshold = rule.threshold_value

        operators = {
            "<": value < threshold,
            "<=": value <= threshold,
            ">": value > threshold,
            ">=": value >= threshold,
            "==": value == threshold,
            "!=": value != threshold,
        }

        return operators.get(operator, False)

    def _evaluate_anomaly(self, rule: AlertRule, value: float) -> bool:
        """이상 탐지 기반 평가"""
        # 간단한 3-sigma 규칙 (실제로는 히스토리 데이터 필요)
        # 데모용으로 임계값의 20% 이상 벗어나면 이상으로 판단
        if not rule.threshold_value:
            return False

        deviation = abs(value - rule.threshold_value) / rule.threshold_value
        sensitivity = rule.anomaly_sensitivity or 0.2

        return deviation > sensitivity

    def _evaluate_trend(self, rule: AlertRule, value: float) -> bool:
        """트렌드 기반 평가"""
        # 최근 N개 값 조회하여 연속 하락/상승 체크
        # 데모용으로 임계값 평가로 대체
        return self._evaluate_threshold(rule, value)

    def _create_alert(
        self,
        rule: AlertRule,
        value: float,
        context: Optional[AlertContext]
    ) -> Alert:
        """알림 생성"""
        alert = Alert(
            alert_id=f"ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
            rule_id=rule.id,
            title=self._generate_alert_title(rule, value),
            message=self._generate_alert_message(rule, value, context),
            severity=rule.severity,
            metric_name=rule.metric,
            metric_value=value,
            threshold_value=rule.threshold_value,
            entity_type=context.entity_type if context else None,
            entity_id=context.entity_id if context else None,
            status="ACTIVE"
        )

        # 규칙 마지막 트리거 시간 업데이트
        rule.last_triggered_at = datetime.utcnow()

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        return alert

    def _generate_alert_title(self, rule: AlertRule, value: float) -> str:
        """알림 제목 생성"""
        severity_emoji = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "🔴",
            "CRITICAL": "🚨"
        }
        emoji = severity_emoji.get(rule.severity, "")
        return f"{emoji} {rule.name}: {rule.metric} = {value:.2f}"

    def _generate_alert_message(
        self,
        rule: AlertRule,
        value: float,
        context: Optional[AlertContext]
    ) -> str:
        """알림 메시지 생성"""
        message_parts = [
            f"규칙: {rule.name}",
            f"메트릭: {rule.metric}",
            f"현재 값: {value:.2f}",
        ]

        if rule.threshold_value:
            message_parts.append(f"임계값: {rule.operator} {rule.threshold_value}")

        if context:
            if context.entity_type and context.entity_id:
                message_parts.append(f"관련 엔티티: {context.entity_type} - {context.entity_id}")

        if rule.description:
            message_parts.append(f"설명: {rule.description}")

        return "\n".join(message_parts)


class NotificationDispatcher:
    """알림 발송 디스패처"""

    def __init__(self, db: Session):
        self.db = db

    def dispatch(self, alert: Alert, recipient_ids: list[str] = None) -> list[NotificationLog]:
        """
        알림 발송

        Args:
            alert: 발송할 알림
            recipient_ids: 특정 수신자 지정 (None이면 규칙 기반)

        Returns:
            발송 로그 목록
        """
        logs = []

        # 수신자 조회
        if recipient_ids:
            recipients = self.db.query(NotificationRecipient).filter(
                NotificationRecipient.recipient_id.in_(recipient_ids),
                NotificationRecipient.is_active == True
            ).all()
        else:
            # 심각도 기반 수신자 필터링
            recipients = self._get_recipients_by_severity(alert.severity)

        # 각 수신자에게 발송
        for recipient in recipients:
            channels = recipient.preferred_channels or ["IN_APP"]

            for channel in channels:
                log = self._send_notification(alert, recipient, channel)
                logs.append(log)

        # 알림 상태 업데이트
        alert.notification_sent = True
        alert.notification_channels = [log.channel_type for log in logs]
        self.db.commit()

        return logs

    def _get_recipients_by_severity(self, severity: str) -> list[NotificationRecipient]:
        """심각도 기반 수신자 조회"""
        recipients = self.db.query(NotificationRecipient).filter(
            NotificationRecipient.is_active == True
        ).all()

        # 심각도 필터 적용
        filtered = []
        for r in recipients:
            if r.severity_filter:
                if severity in r.severity_filter:
                    filtered.append(r)
            else:
                # 필터 없으면 모두 수신
                filtered.append(r)

        return filtered

    def _send_notification(
        self,
        alert: Alert,
        recipient: NotificationRecipient,
        channel_type: str
    ) -> NotificationLog:
        """개별 알림 전송"""
        log = NotificationLog(
            log_id=f"NLOG-{uuid.uuid4().hex[:12].upper()}",
            alert_id=alert.alert_id,
            recipient_id=recipient.recipient_id,
            channel_type=channel_type,
            status="PENDING"
        )

        try:
            if channel_type == "EMAIL":
                self._send_email(alert, recipient)
            elif channel_type == "SLACK":
                self._send_slack(alert, recipient)
            elif channel_type == "SMS":
                self._send_sms(alert, recipient)
            elif channel_type == "IN_APP":
                self._send_in_app(alert, recipient)
            elif channel_type == "WEBHOOK":
                self._send_webhook(alert, recipient)

            log.status = "SENT"
            log.sent_at = datetime.utcnow()

        except Exception as e:
            log.status = "FAILED"
            log.error_message = str(e)
            log.retry_count = 0
            log.next_retry_at = datetime.utcnow() + timedelta(minutes=5)

        self.db.add(log)
        self.db.commit()

        return log

    def _send_email(self, alert: Alert, recipient: NotificationRecipient):
        """이메일 발송 (데모)"""
        # 실제 구현 시 SMTP 또는 SendGrid 등 사용
        print(f"[EMAIL] Sending to {recipient.email}: {alert.title}")

    def _send_slack(self, alert: Alert, recipient: NotificationRecipient):
        """Slack 발송 (데모)"""
        # 실제 구현 시 Slack Webhook 사용
        print(f"[SLACK] Sending to {recipient.slack_user_id}: {alert.title}")

    def _send_sms(self, alert: Alert, recipient: NotificationRecipient):
        """SMS 발송 (데모)"""
        # 실제 구현 시 Twilio 등 사용
        print(f"[SMS] Sending to {recipient.phone}: {alert.title}")

    def _send_in_app(self, alert: Alert, recipient: NotificationRecipient):
        """인앱 알림 (데모)"""
        # WebSocket 또는 SSE로 실시간 전송
        print(f"[IN_APP] Notification for {recipient.name}: {alert.title}")

    def _send_webhook(self, alert: Alert, recipient: NotificationRecipient):
        """Webhook 발송 (데모)"""
        # 실제 구현 시 HTTP POST 요청
        print(f"[WEBHOOK] Sending alert {alert.alert_id}")


class NotificationService:
    """통합 알림 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.rule_engine = AlertRuleEngine(db)
        self.dispatcher = NotificationDispatcher(db)

    # ==================== 알림 규칙 관리 ====================

    def create_rule(
        self,
        name: str,
        metric: str,
        rule_type: str,
        severity: str,
        operator: str = "<",
        threshold_value: float = None,
        **kwargs
    ) -> AlertRule:
        """알림 규칙 생성"""
        rule = AlertRule(
            rule_id=f"RULE-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            metric=metric,
            rule_type=rule_type,
            severity=severity,
            operator=operator,
            threshold_value=threshold_value,
            is_active=True,
            **kwargs
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return rule

    def get_rules(
        self,
        category: str = None,
        is_active: bool = None,
        limit: int = 100
    ) -> list[AlertRule]:
        """알림 규칙 목록"""
        query = self.db.query(AlertRule)

        if category:
            query = query.filter(AlertRule.category == category)
        if is_active is not None:
            query = query.filter(AlertRule.is_active == is_active)

        return query.limit(limit).all()

    def update_rule(self, rule_id: str, **updates) -> AlertRule:
        """알림 규칙 업데이트"""
        rule = self.db.query(AlertRule).filter(AlertRule.rule_id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")

        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        self.db.commit()
        self.db.refresh(rule)

        return rule

    def mute_rule(self, rule_id: str, duration_minutes: int = 60) -> AlertRule:
        """규칙 일시 음소거"""
        rule = self.db.query(AlertRule).filter(AlertRule.rule_id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")

        rule.is_muted = True
        rule.mute_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.db.commit()

        return rule

    # ==================== 알림 관리 ====================

    def get_alerts(
        self,
        status: str = None,
        severity: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> list[Alert]:
        """알림 목록 조회"""
        query = self.db.query(Alert)

        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        if start_date:
            query = query.filter(Alert.triggered_at >= start_date)
        if end_date:
            query = query.filter(Alert.triggered_at <= end_date)

        return query.order_by(Alert.triggered_at.desc()).limit(limit).all()

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> Alert:
        """알림 확인"""
        alert = self.db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")

        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        self.db.commit()

        return alert

    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_notes: str = None
    ) -> Alert:
        """알림 해결"""
        alert = self.db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")

        alert.status = "RESOLVED"
        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.utcnow()
        alert.resolution_notes = resolution_notes
        self.db.commit()

        return alert

    # ==================== 수신자 관리 ====================

    def create_recipient(
        self,
        name: str,
        email: str = None,
        phone: str = None,
        slack_user_id: str = None,
        role: str = None,
        preferred_channels: list = None,
        escalation_level: int = 1
    ) -> NotificationRecipient:
        """수신자 등록"""
        recipient = NotificationRecipient(
            recipient_id=f"RCPT-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            email=email,
            phone=phone,
            slack_user_id=slack_user_id,
            role=role,
            preferred_channels=preferred_channels or ["IN_APP"],
            escalation_level=escalation_level,
            is_active=True
        )

        self.db.add(recipient)
        self.db.commit()
        self.db.refresh(recipient)

        return recipient

    def get_recipients(self, escalation_level: int = None) -> list[NotificationRecipient]:
        """수신자 목록"""
        query = self.db.query(NotificationRecipient).filter(
            NotificationRecipient.is_active == True
        )

        if escalation_level:
            query = query.filter(NotificationRecipient.escalation_level == escalation_level)

        return query.all()

    # ==================== 실시간 모니터링 ====================

    def check_and_alert(self, metrics: dict[str, float]) -> list[Alert]:
        """
        메트릭 체크 및 알림 발송

        Args:
            metrics: 모니터링 메트릭 딕셔너리

        Returns:
            발생한 알림 목록
        """
        # 규칙 평가
        alerts = self.rule_engine.evaluate_all_rules(metrics)

        # 알림 발송
        for alert in alerts:
            self.dispatcher.dispatch(alert)

        return alerts

    def get_alert_summary(self, hours: int = 24) -> dict:
        """알림 요약"""
        start_time = datetime.utcnow() - timedelta(hours=hours)

        alerts = self.db.query(Alert).filter(
            Alert.triggered_at >= start_time
        ).all()

        by_severity = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        by_status = {"ACTIVE": 0, "ACKNOWLEDGED": 0, "RESOLVED": 0}

        for alert in alerts:
            if alert.severity in by_severity:
                by_severity[alert.severity] += 1
            if alert.status in by_status:
                by_status[alert.status] += 1

        return {
            "period_hours": hours,
            "total_alerts": len(alerts),
            "by_severity": by_severity,
            "by_status": by_status,
            "active_critical": len([a for a in alerts if a.severity == "CRITICAL" and a.status == "ACTIVE"]),
            "unacknowledged": len([a for a in alerts if a.status == "ACTIVE"])
        }


# ==================== 기본 규칙 초기화 ====================

def initialize_default_alert_rules(db: Session):
    """기본 알림 규칙 초기화"""
    service = NotificationService(db)

    default_rules = [
        {
            "name": "수율 임계값 경고",
            "metric": "overall_yield",
            "rule_type": "THRESHOLD",
            "severity": "WARNING",
            "operator": "<",
            "threshold_value": 90.0,
            "category": "YIELD",
            "description": "전체 수율이 90% 미만일 때 경고"
        },
        {
            "name": "수율 긴급 알림",
            "metric": "overall_yield",
            "rule_type": "THRESHOLD",
            "severity": "CRITICAL",
            "operator": "<",
            "threshold_value": 85.0,
            "category": "YIELD",
            "description": "전체 수율이 85% 미만일 때 긴급 알림"
        },
        {
            "name": "장비 가동률 저하",
            "metric": "equipment_oee",
            "rule_type": "THRESHOLD",
            "severity": "WARNING",
            "operator": "<",
            "threshold_value": 80.0,
            "category": "EQUIPMENT",
            "description": "장비 OEE가 80% 미만일 때 경고"
        },
        {
            "name": "재고 부족 경고",
            "metric": "inventory_level",
            "rule_type": "THRESHOLD",
            "severity": "WARNING",
            "operator": "<",
            "threshold_value": 20.0,
            "category": "SUPPLY_CHAIN",
            "description": "재고가 안전재고 대비 20% 미만일 때 경고"
        },
        {
            "name": "공급망 리스크 감지",
            "metric": "supply_risk_score",
            "rule_type": "THRESHOLD",
            "severity": "ERROR",
            "operator": ">",
            "threshold_value": 70.0,
            "category": "SUPPLY_CHAIN",
            "description": "공급망 리스크 점수가 70 초과 시 알림"
        }
    ]

    for rule_data in default_rules:
        existing = db.query(AlertRule).filter(AlertRule.name == rule_data["name"]).first()
        if not existing:
            service.create_rule(**rule_data)
