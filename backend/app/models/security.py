"""
Security Models

사용자, 역할, 권한, 감사 로그 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


# 사용자-역할 다대다 관계
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)


class User(Base):
    """사용자"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    name = Column(String(100))
    department = Column(String(100))

    # 인증
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # 외부 파트너 여부
    is_external = Column(Boolean, default=False)
    company = Column(String(100))  # 외부 파트너의 회사명

    # 타임스탬프
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    roles = relationship("Role", secondary=user_roles, back_populates="users")


class Role(Base):
    """역할"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))

    # 권한 정의 (JSON)
    permissions = Column(JSON)  # {"yield": ["read"], "recipe": ["read", "write"]}

    # 데이터 마스킹 규칙
    masking_rules = Column(JSON)  # {"yield_percent": "range", "cost": "hide"}

    # 접근 제한 조건
    conditions = Column(JSON)  # {"time_range": "9-18", "ip_whitelist": [...]}

    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    users = relationship("User", secondary=user_roles, back_populates="roles")


class AccessPolicy(Base):
    """접근 정책 (세밀한 접근 제어)"""
    __tablename__ = "access_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))

    # 적용 대상
    roles = Column(JSON)  # ["Partner_ASML", "Partner_Samsung"]
    users = Column(JSON)  # 특정 사용자 직접 지정

    # 리소스 및 액션
    resources = Column(JSON)  # ["yield.*", "equipment.utilization"]
    actions = Column(JSON)  # ["read", "write", "delete", "export"]
    effect = Column(String(10))  # "allow" or "deny"

    # 조건
    conditions = Column(JSON)  # {"time": "09:00-18:00", "ip_range": "..."}

    # 유효 기간
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """감사 로그"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 사용자 정보
    user_id = Column(String(50), index=True)
    user_name = Column(String(100))
    user_role = Column(String(50))

    # 액션 정보
    action = Column(String(50), index=True)  # VIEW, CREATE, UPDATE, DELETE, EXPORT, LOGIN
    resource = Column(String(100), index=True)  # yield_events, wafer_records, etc.
    resource_id = Column(String(50))

    # 결과
    result = Column(String(20))  # SUCCESS, DENIED, ERROR

    # 상세 정보
    details = Column(JSON)  # 추가 컨텍스트
    request_data = Column(JSON)  # 요청 데이터 (민감 정보 제외)

    # 클라이언트 정보
    ip_address = Column(String(50))
    user_agent = Column(String(500))

    # 타임스탬프
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class DataMaskingRule(Base):
    """데이터 마스킹 규칙"""
    __tablename__ = "data_masking_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(50), unique=True, nullable=False)

    # 적용 대상
    field_path = Column(String(200), nullable=False)  # "yield_event.yield_percent"
    roles = Column(JSON)  # 적용할 역할들

    # 마스킹 방식
    mask_type = Column(String(20))  # HIDE, RANGE, HASH, PARTIAL
    mask_config = Column(JSON)  # {"ranges": [[0,70,"Low"], [70,90,"Medium"], [90,100,"High"]]}

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
