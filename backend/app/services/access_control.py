"""
Access Control Service

Role-Based + Attribute-Based Access Control (RBAC + ABAC)
Palantir-grade Security Layer
"""

from datetime import datetime
from typing import Optional, Any
from functools import wraps
import hashlib
import re

from sqlalchemy.orm import Session

from app.models.security import (
    User, Role, AccessPolicy, AuditLog, DataMaskingRule
)


class AccessControlEngine:
    """
    RBAC + ABAC 기반 접근 제어 엔진

    기능:
    - Role 기반 권한 관리
    - Attribute 기반 조건부 접근 제어
    - 리소스별 세분화된 권한 체크
    - 데이터 마스킹 정책 적용
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== 사용자 관리 ====================

    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        department: Optional[str] = None,
        role_names: Optional[list[str]] = None
    ) -> User:
        """사용자 생성"""
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            department=department,
            is_active=True
        )

        if role_names:
            roles = self.db.query(Role).filter(Role.name.in_(role_names)).all()
            user.roles = roles

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """사용자 조회"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 조회"""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_roles(self, user_id: int) -> list[Role]:
        """사용자의 역할 목록"""
        user = self.get_user(user_id)
        return user.roles if user else []

    def assign_role(self, user_id: int, role_name: str) -> bool:
        """사용자에게 역할 할당"""
        user = self.get_user(user_id)
        role = self.db.query(Role).filter(Role.name == role_name).first()

        if user and role:
            if role not in user.roles:
                user.roles.append(role)
                self.db.commit()
            return True
        return False

    def revoke_role(self, user_id: int, role_name: str) -> bool:
        """사용자에서 역할 제거"""
        user = self.get_user(user_id)
        role = self.db.query(Role).filter(Role.name == role_name).first()

        if user and role and role in user.roles:
            user.roles.remove(role)
            self.db.commit()
            return True
        return False

    # ==================== 역할 관리 ====================

    def create_role(
        self,
        name: str,
        description: str,
        permissions: list[str],
        level: int = 1
    ) -> Role:
        """역할 생성"""
        role = Role(
            name=name,
            description=description,
            permissions=permissions,
            level=level,
            is_active=True
        )

        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def get_role(self, role_name: str) -> Optional[Role]:
        """역할 조회"""
        return self.db.query(Role).filter(Role.name == role_name).first()

    def get_all_roles(self) -> list[Role]:
        """모든 역할 목록"""
        return self.db.query(Role).filter(Role.is_active == True).all()

    # ==================== 정책 관리 ====================

    def create_policy(
        self,
        name: str,
        description: str,
        roles: list[str],
        resources: list[str],
        actions: list[str],
        conditions: Optional[list[dict]] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None
    ) -> AccessPolicy:
        """접근 정책 생성"""
        import uuid

        policy = AccessPolicy(
            policy_id=f"POL-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            description=description,
            roles=roles,
            resources=resources,
            actions=actions,
            conditions=conditions or [],
            is_active=True,
            valid_from=valid_from or datetime.utcnow(),
            valid_until=valid_until
        )

        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def get_policies_for_role(self, role_name: str) -> list[AccessPolicy]:
        """역할에 적용되는 정책 목록"""
        policies = self.db.query(AccessPolicy).filter(
            AccessPolicy.is_active == True
        ).all()

        return [p for p in policies if role_name in p.roles]

    # ==================== 접근 제어 ====================

    def check_access(
        self,
        user_id: int,
        resource: str,
        action: str,
        context: Optional[dict] = None
    ) -> tuple[bool, str]:
        """
        접근 권한 체크

        Args:
            user_id: 사용자 ID
            resource: 리소스 패턴 (예: "yield:events", "fab:equipment:*")
            action: 액션 (VIEW, EDIT, DELETE, EXPORT)
            context: 추가 컨텍스트 (IP, 시간 등)

        Returns:
            (허용여부, 사유)
        """
        user = self.get_user(user_id)
        if not user:
            return False, "User not found"

        if not user.is_active:
            return False, "User is deactivated"

        # 사용자의 모든 역할 수집
        user_roles = [role.name for role in user.roles]

        if not user_roles:
            return False, "User has no roles assigned"

        # Admin은 항상 허용
        if "admin" in user_roles or "system_admin" in user_roles:
            return True, "Admin access granted"

        # 역할별 정책 확인
        for role_name in user_roles:
            policies = self.get_policies_for_role(role_name)

            for policy in policies:
                # 정책 유효 기간 체크
                if not self._is_policy_valid(policy):
                    continue

                # 리소스 매칭
                if not self._match_resource(resource, policy.resources):
                    continue

                # 액션 매칭
                if action not in policy.actions and "*" not in policy.actions:
                    continue

                # 조건 평가
                if policy.conditions:
                    if not self._evaluate_conditions(policy.conditions, context or {}):
                        continue

                return True, f"Access granted by policy: {policy.name}"

        return False, "No matching policy found"

    def _is_policy_valid(self, policy: AccessPolicy) -> bool:
        """정책 유효 기간 체크"""
        now = datetime.utcnow()

        if policy.valid_from and now < policy.valid_from:
            return False

        if policy.valid_until and now > policy.valid_until:
            return False

        return True

    def _match_resource(self, requested: str, allowed: list[str]) -> bool:
        """리소스 패턴 매칭"""
        for pattern in allowed:
            if pattern == "*":
                return True

            if pattern == requested:
                return True

            # 와일드카드 패턴 매칭
            if "*" in pattern:
                regex = pattern.replace("*", ".*")
                if re.match(f"^{regex}$", requested):
                    return True

        return False

    def _evaluate_conditions(
        self,
        conditions: list[dict],
        context: dict
    ) -> bool:
        """ABAC 조건 평가"""
        for condition in conditions:
            cond_type = condition.get("type")
            operator = condition.get("operator", "EQUALS")
            value = condition.get("value")

            # 시간 조건
            if cond_type == "TIME":
                current_hour = datetime.utcnow().hour
                if operator == "BETWEEN":
                    start, end = value
                    if not (start <= current_hour <= end):
                        return False
                elif operator == "IN":
                    if current_hour not in value:
                        return False

            # IP 범위 조건
            elif cond_type == "IP_RANGE":
                client_ip = context.get("ip_address", "")
                if not self._check_ip_range(client_ip, value):
                    return False

            # 지역 조건
            elif cond_type == "GEOGRAPHY":
                client_geo = context.get("geography", "")
                if operator == "IN":
                    if client_geo not in value:
                        return False
                elif operator == "NOT_IN":
                    if client_geo in value:
                        return False

            # 계약 기간 조건
            elif cond_type == "CONTRACT":
                contract_active = context.get("contract_active", False)
                if not contract_active:
                    return False

        return True

    def _check_ip_range(self, ip: str, allowed_ranges: list[str]) -> bool:
        """IP 범위 체크"""
        if not ip:
            return False

        for ip_range in allowed_ranges:
            # CIDR 표기법 지원 (간단한 구현)
            if "/" in ip_range:
                # 실제로는 ipaddress 모듈 사용 권장
                network = ip_range.split("/")[0]
                if ip.startswith(network.rsplit(".", 1)[0]):
                    return True
            elif ip == ip_range:
                return True
            elif ip_range == "*":
                return True

        return False

    # ==================== 권한 편의 메서드 ====================

    def can_view(self, user_id: int, resource: str, context: dict = None) -> bool:
        """VIEW 권한 체크"""
        allowed, _ = self.check_access(user_id, resource, "VIEW", context)
        return allowed

    def can_edit(self, user_id: int, resource: str, context: dict = None) -> bool:
        """EDIT 권한 체크"""
        allowed, _ = self.check_access(user_id, resource, "EDIT", context)
        return allowed

    def can_delete(self, user_id: int, resource: str, context: dict = None) -> bool:
        """DELETE 권한 체크"""
        allowed, _ = self.check_access(user_id, resource, "DELETE", context)
        return allowed

    def can_export(self, user_id: int, resource: str, context: dict = None) -> bool:
        """EXPORT 권한 체크"""
        allowed, _ = self.check_access(user_id, resource, "EXPORT", context)
        return allowed


# ==================== 기본 역할 및 정책 초기화 ====================

def initialize_default_roles(db: Session):
    """기본 역할 초기화"""
    ace = AccessControlEngine(db)

    default_roles = [
        {
            "name": "admin",
            "description": "시스템 관리자 - 전체 접근 권한",
            "permissions": ["*"],
            "level": 100
        },
        {
            "name": "engineer",
            "description": "엔지니어 - 수율/공정 데이터 접근",
            "permissions": ["yield:read", "yield:write", "fab:read", "reports:read"],
            "level": 50
        },
        {
            "name": "operator",
            "description": "운영자 - 읽기 전용 접근",
            "permissions": ["yield:read", "fab:read", "reports:read"],
            "level": 20
        },
        {
            "name": "partner",
            "description": "파트너사 - 제한된 접근 (마스킹 적용)",
            "permissions": ["equipment:read:masked", "maintenance:read"],
            "level": 10
        },
        {
            "name": "auditor",
            "description": "감사자 - 읽기 전용 + 감사 로그 접근",
            "permissions": ["*:read", "audit:read"],
            "level": 30
        }
    ]

    for role_data in default_roles:
        existing = ace.get_role(role_data["name"])
        if not existing:
            ace.create_role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                level=role_data["level"]
            )


def initialize_default_policies(db: Session):
    """기본 접근 정책 초기화"""
    ace = AccessControlEngine(db)

    default_policies = [
        {
            "name": "Engineer Full Access",
            "description": "엔지니어 수율/공정 전체 접근",
            "roles": ["engineer", "admin"],
            "resources": ["yield:*", "fab:*", "reports:*"],
            "actions": ["VIEW", "EDIT", "EXPORT"],
            "conditions": []
        },
        {
            "name": "Partner Limited Access",
            "description": "파트너사 장비 상태 제한 접근",
            "roles": ["partner"],
            "resources": ["equipment:status", "maintenance:schedule"],
            "actions": ["VIEW"],
            "conditions": [
                {"type": "CONTRACT", "operator": "EQUALS", "value": True},
                {"type": "TIME", "operator": "BETWEEN", "value": [9, 18]}
            ]
        },
        {
            "name": "Operator Read Only",
            "description": "운영자 읽기 전용 접근",
            "roles": ["operator"],
            "resources": ["yield:events", "yield:dashboard", "fab:status"],
            "actions": ["VIEW"],
            "conditions": []
        }
    ]

    for policy_data in default_policies:
        ace.create_policy(
            name=policy_data["name"],
            description=policy_data["description"],
            roles=policy_data["roles"],
            resources=policy_data["resources"],
            actions=policy_data["actions"],
            conditions=policy_data.get("conditions")
        )
