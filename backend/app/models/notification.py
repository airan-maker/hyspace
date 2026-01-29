"""
Notification Models

알림 및 알림 규칙 관리 데이터 모델
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NotificationChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    SLACK = "SLACK"
    SMS = "SMS"
    IN_APP = "IN_APP"
    WEBHOOK = "WEBHOOK"


class AlertRuleType(str, enum.Enum):
    THRESHOLD = "THRESHOLD"  # 임계값 기반
    ANOMALY = "ANOMALY"  # 이상 탐지 기반
    TREND = "TREND"  # 트렌드 기반
    EVENT = "EVENT"  # 이벤트 기반


# 알림 규칙-채널 연결 테이블
alert_rule_channels = Table(
    'alert_rule_channels',
    Base.metadata,
    Column('alert_rule_id', Integer, ForeignKey('alert_rules.id'), primary_key=True),
    Column('notification_channel_id', Integer, ForeignKey('notification_channels.id'), primary_key=True)
)

# 알림 규칙-수신자 연결 테이블
alert_rule_recipients = Table(
    'alert_rule_recipients',
    Base.metadata,
    Column('alert_rule_id', Integer, ForeignKey('alert_rules.id'), primary_key=True),
    Column('recipient_id', Integer, ForeignKey('notification_recipients.id'), primary_key=True)
)


class AlertRule(Base):
    """알림 규칙 모델"""
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))

    # 규칙 유형
    rule_type = Column(String(50), nullable=False)  # THRESHOLD, ANOMALY, TREND, EVENT
    category = Column(String(50))  # YIELD, EQUIPMENT, SUPPLY_CHAIN, SECURITY

    # 조건 정의
    metric = Column(String(100), nullable=False)  # 모니터링 대상 메트릭
    operator = Column(String(20))  # <, <=, >, >=, ==, !=
    threshold_value = Column(Float)  # 임계값
    threshold_unit = Column(String(20))  # %, count, etc.

    # 트렌드 조건 (연속 N회)
    consecutive_count = Column(Integer)  # 연속 발생 횟수
    time_window_minutes = Column(Integer)  # 시간 윈도우

    # 이상 탐지 설정
    anomaly_method = Column(String(50))  # 3_SIGMA, MAD, ISOLATION_FOREST
    anomaly_sensitivity = Column(Float)  # 민감도 (0-1)

    # 심각도
    severity = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, CRITICAL

    # 에스컬레이션
    escalation_enabled = Column(Boolean, default=False)
    escalation_delay_minutes = Column(Integer)  # 에스컬레이션 대기 시간
    escalation_level = Column(Integer, default=1)  # 현재 에스컬레이션 레벨

    # 쿨다운 (중복 알림 방지)
    cooldown_minutes = Column(Integer, default=30)
    last_triggered_at = Column(DateTime)

    # 상태
    is_active = Column(Boolean, default=True)
    is_muted = Column(Boolean, default=False)
    mute_until = Column(DateTime)

    # 메타데이터
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    alerts = relationship("Alert", back_populates="rule")


class NotificationChannelConfig(Base):
    """알림 채널 설정 모델"""
    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    channel_type = Column(String(20), nullable=False)  # EMAIL, SLACK, SMS, IN_APP, WEBHOOK

    # 채널별 설정
    config = Column(JSON)
    """
    EMAIL: {"smtp_host": "...", "smtp_port": 587, "username": "...", "from_address": "..."}
    SLACK: {"webhook_url": "...", "channel": "#alerts"}
    SMS: {"provider": "twilio", "account_sid": "...", "auth_token": "...", "from_number": "..."}
    WEBHOOK: {"url": "...", "method": "POST", "headers": {...}}
    """

    # 상태
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    failure_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationRecipient(Base):
    """알림 수신자 모델"""
    __tablename__ = "notification_recipients"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(50))  # ENGINEER, MANAGER, EXECUTIVE

    # 연락처
    email = Column(String(200))
    phone = Column(String(50))
    slack_user_id = Column(String(50))

    # 알림 선호 설정
    preferred_channels = Column(JSON)  # ["EMAIL", "SLACK"]
    severity_filter = Column(JSON)  # ["ERROR", "CRITICAL"] - 이 심각도만 수신
    quiet_hours = Column(JSON)  # {"start": "22:00", "end": "07:00"}

    # 에스컬레이션 레벨
    escalation_level = Column(Integer, default=1)  # 1: 담당자, 2: 팀장, 3: 임원

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    """발생한 알림 모델"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(50), unique=True, index=True, nullable=False)

    # 연결된 규칙
    rule_id = Column(Integer, ForeignKey("alert_rules.id"))

    # 알림 내용
    title = Column(String(300), nullable=False)
    message = Column(String(2000))
    severity = Column(String(20), nullable=False)

    # 트리거 정보
    metric_name = Column(String(100))
    metric_value = Column(Float)
    threshold_value = Column(Float)
    triggered_at = Column(DateTime, default=datetime.utcnow)

    # 관련 엔티티
    entity_type = Column(String(50))  # EQUIPMENT, LOT, SUPPLIER, etc.
    entity_id = Column(String(100))

    # 상태
    status = Column(String(20), default="ACTIVE")  # ACTIVE, ACKNOWLEDGED, RESOLVED, EXPIRED
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    resolution_notes = Column(String(1000))

    # 알림 전송 상태
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(JSON)  # 전송된 채널 목록
    notification_errors = Column(JSON)  # 전송 실패 기록

    # 에스컬레이션
    escalation_level = Column(Integer, default=1)
    escalated_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rule = relationship("AlertRule", back_populates="alerts")


class NotificationLog(Base):
    """알림 전송 로그 모델"""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(50), unique=True, index=True, nullable=False)

    alert_id = Column(String(50), nullable=False)
    recipient_id = Column(String(50))
    channel_type = Column(String(20), nullable=False)

    # 전송 상태
    status = Column(String(20), nullable=False)  # PENDING, SENT, FAILED, BOUNCED
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)

    # 에러 정보
    error_message = Column(String(500))
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime)

    # 응답 정보
    external_message_id = Column(String(200))  # 외부 서비스 메시지 ID
    response_data = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
