"""
Security API Endpoints

접근 제어, 감사 로그, 데이터 마스킹 관리 API
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.access_control import AccessControlEngine
from app.services.audit_logger import AuditLogger
from app.services.data_masking import DataMaskingService
from app.models.security import User, Role, AccessPolicy, AuditLog, DataMaskingRule

router = APIRouter(prefix="/security", tags=["Security & Governance"])


# ==================== Schemas ====================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    department: Optional[str] = None
    role_names: Optional[list[str]] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    department: Optional[str]
    is_active: bool
    created_at: datetime
    roles: list[str]

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    name: str
    description: str
    permissions: list[str]
    level: int = 1


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str
    permissions: list[str]
    level: int
    is_active: bool

    class Config:
        from_attributes = True


class PolicyCreate(BaseModel):
    name: str
    description: str
    roles: list[str]
    resources: list[str]
    actions: list[str]
    conditions: Optional[list[dict]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class PolicyResponse(BaseModel):
    id: int
    policy_id: str
    name: str
    description: str
    roles: list[str]
    resources: list[str]
    actions: list[str]
    conditions: list[dict]
    is_active: bool
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]

    class Config:
        from_attributes = True


class AccessCheckRequest(BaseModel):
    user_id: int
    resource: str
    action: str
    context: Optional[dict] = None


class AccessCheckResponse(BaseModel):
    allowed: bool
    reason: str


class AuditLogResponse(BaseModel):
    id: int
    log_id: str
    timestamp: datetime
    user_id: int
    user_role: str
    action: str
    resource: str
    resource_id: Optional[str]
    result: str
    ip_address: Optional[str]
    details: Optional[dict]

    class Config:
        from_attributes = True


class MaskingRuleCreate(BaseModel):
    name: str
    resource: str
    field: str
    mask_type: str
    mask_config: Optional[dict] = None
    applies_to_roles: Optional[list[str]] = None
    description: Optional[str] = None


class MaskingRuleResponse(BaseModel):
    id: int
    rule_id: str
    name: str
    description: Optional[str]
    resource: str
    field: str
    mask_type: str
    mask_config: dict
    applies_to_roles: list[str]
    is_active: bool

    class Config:
        from_attributes = True


# ==================== Users ====================

@router.post("/users", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """사용자 생성"""
    ace = AccessControlEngine(db)

    # 중복 체크
    existing = ace.get_user_by_username(user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    # 비밀번호 해시 (실제로는 bcrypt 등 사용)
    import hashlib
    password_hash = hashlib.sha256(user.password.encode()).hexdigest()

    db_user = ace.create_user(
        username=user.username,
        email=user.email,
        password_hash=password_hash,
        department=user.department,
        role_names=user.role_names
    )

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="CREATE",
        resource="user",
        resource_id=str(db_user.id),
        details={"username": user.username}
    )

    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        department=db_user.department,
        is_active=db_user.is_active,
        created_at=db_user.created_at,
        roles=[r.name for r in db_user.roles]
    )


@router.get("/users", response_model=list[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """사용자 목록 조회"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            department=u.department,
            is_active=u.is_active,
            created_at=u.created_at,
            roles=[r.name for r in u.roles]
        )
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """특정 사용자 조회"""
    ace = AccessControlEngine(db)
    user = ace.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        department=user.department,
        is_active=user.is_active,
        created_at=user.created_at,
        roles=[r.name for r in user.roles]
    )


@router.post("/users/{user_id}/roles/{role_name}")
def assign_role_to_user(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db)
):
    """사용자에게 역할 할당"""
    ace = AccessControlEngine(db)
    success = ace.assign_role(user_id, role_name)

    if not success:
        raise HTTPException(status_code=404, detail="User or role not found")

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="ASSIGN_ROLE",
        resource="user",
        resource_id=str(user_id),
        details={"role": role_name}
    )

    return {"message": f"Role '{role_name}' assigned to user {user_id}"}


@router.delete("/users/{user_id}/roles/{role_name}")
def revoke_role_from_user(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db)
):
    """사용자에서 역할 제거"""
    ace = AccessControlEngine(db)
    success = ace.revoke_role(user_id, role_name)

    if not success:
        raise HTTPException(status_code=404, detail="User or role not found")

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="REVOKE_ROLE",
        resource="user",
        resource_id=str(user_id),
        details={"role": role_name}
    )

    return {"message": f"Role '{role_name}' revoked from user {user_id}"}


# ==================== Roles ====================

@router.post("/roles", response_model=RoleResponse)
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db)
):
    """역할 생성"""
    ace = AccessControlEngine(db)

    # 중복 체크
    existing = ace.get_role(role.name)
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")

    db_role = ace.create_role(
        name=role.name,
        description=role.description,
        permissions=role.permissions,
        level=role.level
    )

    return db_role


@router.get("/roles", response_model=list[RoleResponse])
def get_roles(db: Session = Depends(get_db)):
    """역할 목록 조회"""
    ace = AccessControlEngine(db)
    return ace.get_all_roles()


@router.get("/roles/{role_name}", response_model=RoleResponse)
def get_role(
    role_name: str,
    db: Session = Depends(get_db)
):
    """특정 역할 조회"""
    ace = AccessControlEngine(db)
    role = ace.get_role(role_name)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


# ==================== Policies ====================

@router.post("/policies", response_model=PolicyResponse)
def create_policy(
    policy: PolicyCreate,
    db: Session = Depends(get_db)
):
    """접근 정책 생성"""
    ace = AccessControlEngine(db)

    db_policy = ace.create_policy(
        name=policy.name,
        description=policy.description,
        roles=policy.roles,
        resources=policy.resources,
        actions=policy.actions,
        conditions=policy.conditions,
        valid_from=policy.valid_from,
        valid_until=policy.valid_until
    )

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="CREATE",
        resource="access_policy",
        resource_id=db_policy.policy_id,
        details={"name": policy.name, "roles": policy.roles}
    )

    return db_policy


@router.get("/policies", response_model=list[PolicyResponse])
def get_policies(
    role: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """접근 정책 목록 조회"""
    query = db.query(AccessPolicy).filter(AccessPolicy.is_active == True)

    if role:
        # 특정 역할에 적용되는 정책만 필터링
        policies = query.all()
        return [p for p in policies if role in p.roles]

    return query.all()


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
def get_policy(
    policy_id: str,
    db: Session = Depends(get_db)
):
    """특정 정책 조회"""
    policy = db.query(AccessPolicy).filter(AccessPolicy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


# ==================== Access Check ====================

@router.post("/access-check", response_model=AccessCheckResponse)
def check_access(
    request: AccessCheckRequest,
    db: Session = Depends(get_db)
):
    """접근 권한 확인"""
    ace = AccessControlEngine(db)
    allowed, reason = ace.check_access(
        user_id=request.user_id,
        resource=request.resource,
        action=request.action,
        context=request.context
    )

    return AccessCheckResponse(allowed=allowed, reason=reason)


# ==================== Audit Logs ====================

@router.get("/audit", response_model=list[AuditLogResponse])
def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    result: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """감사 로그 조회"""
    audit = AuditLogger(db)
    logs = audit.get_logs(
        user_id=user_id,
        action=action,
        resource=resource,
        result=result,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=skip
    )
    return logs


@router.get("/audit/summary")
def get_audit_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """감사 로그 요약 통계"""
    audit = AuditLogger(db)
    return audit.get_activity_summary(days=days)


@router.get("/audit/trend")
def get_audit_trend(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """일별 활동 트렌드"""
    audit = AuditLogger(db)
    return audit.get_daily_trend(days=days)


@router.get("/audit/user/{user_id}", response_model=list[AuditLogResponse])
def get_user_activity(
    user_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """특정 사용자 활동 로그"""
    audit = AuditLogger(db)
    return audit.get_user_activity(user_id=user_id, days=days)


@router.get("/audit/resource/{resource}/{resource_id}", response_model=list[AuditLogResponse])
def get_resource_history(
    resource: str,
    resource_id: str,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """특정 리소스 변경 이력"""
    audit = AuditLogger(db)
    return audit.get_resource_history(
        resource=resource,
        resource_id=resource_id,
        limit=limit
    )


@router.get("/audit/security-events", response_model=list[AuditLogResponse])
def get_security_events(
    severity: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """보안 이벤트 조회"""
    audit = AuditLogger(db)
    return audit.get_security_events(severity=severity, days=days)


@router.get("/audit/failed-logins", response_model=list[AuditLogResponse])
def get_failed_logins(
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """실패한 로그인 시도 조회"""
    audit = AuditLogger(db)
    return audit.get_failed_logins(hours=hours)


@router.post("/audit/export")
def export_audit_logs(
    start_date: datetime,
    end_date: datetime,
    format: str = Query(default="json", regex="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """감사 로그 내보내기"""
    audit = AuditLogger(db)
    content = audit.export_logs(start_date, end_date, format=format)

    # 감사 로그 (내보내기 기록)
    audit.log_export(
        user_id=0,
        user_role="system",
        resource="audit_logs",
        export_format=format,
        record_count=len(content.split("\n")) if format == "csv" else content.count('"log_id"')
    )

    return {
        "format": format,
        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "content": content
    }


@router.post("/audit/report")
def generate_compliance_report(
    start_date: datetime,
    end_date: datetime,
    report_type: str = "full",
    db: Session = Depends(get_db)
):
    """컴플라이언스 보고서 생성"""
    audit = AuditLogger(db)
    return audit.generate_compliance_report(start_date, end_date, report_type)


# ==================== Data Masking ====================

@router.post("/masking/rules", response_model=MaskingRuleResponse)
def create_masking_rule(
    rule: MaskingRuleCreate,
    db: Session = Depends(get_db)
):
    """마스킹 규칙 생성"""
    dms = DataMaskingService(db)

    db_rule = dms.create_rule(
        name=rule.name,
        resource=rule.resource,
        field=rule.field,
        mask_type=rule.mask_type,
        mask_config=rule.mask_config,
        applies_to_roles=rule.applies_to_roles,
        description=rule.description
    )

    # 감사 로그
    audit = AuditLogger(db)
    audit.log(
        user_id=0,
        user_role="system",
        action="CREATE",
        resource="masking_rule",
        resource_id=db_rule.rule_id,
        details={"name": rule.name, "mask_type": rule.mask_type}
    )

    return db_rule


@router.get("/masking/rules", response_model=list[MaskingRuleResponse])
def get_masking_rules(
    resource: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """마스킹 규칙 목록 조회"""
    query = db.query(DataMaskingRule).filter(DataMaskingRule.is_active == True)

    if resource:
        query = query.filter(DataMaskingRule.resource == resource)

    return query.all()


@router.get("/masking/rules/{rule_id}", response_model=MaskingRuleResponse)
def get_masking_rule(
    rule_id: str,
    db: Session = Depends(get_db)
):
    """특정 마스킹 규칙 조회"""
    rule = db.query(DataMaskingRule).filter(DataMaskingRule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Masking rule not found")
    return rule


@router.post("/masking/test")
def test_masking(
    data: dict,
    resource: str,
    user_role: str,
    db: Session = Depends(get_db)
):
    """마스킹 테스트"""
    dms = DataMaskingService(db)
    masked = dms.mask_data(data, resource, user_role)
    return {
        "original": data,
        "masked": masked,
        "resource": resource,
        "user_role": user_role
    }
