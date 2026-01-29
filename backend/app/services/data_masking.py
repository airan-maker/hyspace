"""
Data Masking Service

민감 데이터 마스킹 서비스
파트너사/외부 사용자에게 제한된 데이터 제공
"""

from datetime import datetime
from typing import Any, Optional
import re
import hashlib

from sqlalchemy.orm import Session

from app.models.security import DataMaskingRule


class DataMaskingService:
    """
    데이터 마스킹 서비스

    마스킹 유형:
    - HIDE: 완전 숨김 (값을 [HIDDEN]으로 대체)
    - HASH: 해시 처리 (복원 불가능한 단방향 해시)
    - PARTIAL: 부분 마스킹 (예: 앞 3자리만 표시)
    - RANGE: 범위로 표현 (예: 정확한 수치 대신 "Above Target")
    - CATEGORY: 범주화 (예: 정확한 값 대신 HIGH/MEDIUM/LOW)
    - NOISE: 노이즈 추가 (통계적 분석용 데이터에 약간의 오차 추가)
    """

    def __init__(self, db: Session):
        self.db = db
        self._rules_cache: dict[str, list[DataMaskingRule]] = {}

    # ==================== 마스킹 규칙 관리 ====================

    def create_rule(
        self,
        name: str,
        resource: str,
        field: str,
        mask_type: str,
        mask_config: Optional[dict] = None,
        applies_to_roles: Optional[list[str]] = None,
        description: Optional[str] = None
    ) -> DataMaskingRule:
        """마스킹 규칙 생성"""
        import uuid

        rule = DataMaskingRule(
            rule_id=f"MASK-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            description=description,
            resource=resource,
            field=field,
            mask_type=mask_type,
            mask_config=mask_config or {},
            applies_to_roles=applies_to_roles or [],
            is_active=True
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        # 캐시 무효화
        self._rules_cache.clear()

        return rule

    def get_rules_for_resource(self, resource: str) -> list[DataMaskingRule]:
        """리소스에 적용되는 마스킹 규칙"""
        if resource in self._rules_cache:
            return self._rules_cache[resource]

        rules = self.db.query(DataMaskingRule).filter(
            DataMaskingRule.resource == resource,
            DataMaskingRule.is_active == True
        ).all()

        self._rules_cache[resource] = rules
        return rules

    def get_rules_for_role(self, role: str) -> list[DataMaskingRule]:
        """역할에 적용되는 마스킹 규칙"""
        rules = self.db.query(DataMaskingRule).filter(
            DataMaskingRule.is_active == True
        ).all()

        return [r for r in rules if role in r.applies_to_roles or "*" in r.applies_to_roles]

    # ==================== 데이터 마스킹 ====================

    def mask_data(
        self,
        data: Any,
        resource: str,
        user_role: str
    ) -> Any:
        """
        데이터 마스킹 적용

        Args:
            data: 원본 데이터 (dict, list, 또는 단일 값)
            resource: 리소스 유형
            user_role: 사용자 역할

        Returns:
            마스킹된 데이터
        """
        # Admin은 마스킹 적용 안함
        if user_role in ["admin", "system_admin"]:
            return data

        rules = self.get_rules_for_resource(resource)
        applicable_rules = [r for r in rules if user_role in r.applies_to_roles or "*" in r.applies_to_roles]

        if not applicable_rules:
            return data

        if isinstance(data, list):
            return [self._mask_item(item, applicable_rules) for item in data]
        elif isinstance(data, dict):
            return self._mask_item(data, applicable_rules)
        else:
            return data

    def _mask_item(self, item: dict, rules: list[DataMaskingRule]) -> dict:
        """단일 아이템 마스킹"""
        if not isinstance(item, dict):
            return item

        masked = item.copy()

        for rule in rules:
            if rule.field in masked:
                original_value = masked[rule.field]
                masked[rule.field] = self._apply_mask(
                    original_value,
                    rule.mask_type,
                    rule.mask_config
                )

            # 중첩 필드 지원 (예: "sensor_data.temperature")
            if "." in rule.field:
                parts = rule.field.split(".")
                if len(parts) == 2 and parts[0] in masked:
                    if isinstance(masked[parts[0]], dict) and parts[1] in masked[parts[0]]:
                        original_value = masked[parts[0]][parts[1]]
                        masked[parts[0]] = masked[parts[0]].copy()
                        masked[parts[0]][parts[1]] = self._apply_mask(
                            original_value,
                            rule.mask_type,
                            rule.mask_config
                        )

        return masked

    def _apply_mask(
        self,
        value: Any,
        mask_type: str,
        config: dict
    ) -> Any:
        """
        마스킹 적용

        Args:
            value: 원본 값
            mask_type: 마스킹 유형
            config: 마스킹 설정

        Returns:
            마스킹된 값
        """
        if value is None:
            return None

        if mask_type == "HIDE":
            return config.get("replacement", "[HIDDEN]")

        elif mask_type == "HASH":
            salt = config.get("salt", "default_salt")
            return hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()[:16]

        elif mask_type == "PARTIAL":
            return self._partial_mask(str(value), config)

        elif mask_type == "RANGE":
            return self._range_mask(value, config)

        elif mask_type == "CATEGORY":
            return self._category_mask(value, config)

        elif mask_type == "NOISE":
            return self._noise_mask(value, config)

        return value

    def _partial_mask(self, value: str, config: dict) -> str:
        """부분 마스킹"""
        show_first = config.get("show_first", 0)
        show_last = config.get("show_last", 0)
        mask_char = config.get("mask_char", "*")

        if len(value) <= show_first + show_last:
            return mask_char * len(value)

        prefix = value[:show_first] if show_first > 0 else ""
        suffix = value[-show_last:] if show_last > 0 else ""
        middle_len = len(value) - show_first - show_last

        return f"{prefix}{mask_char * middle_len}{suffix}"

    def _range_mask(self, value: Any, config: dict) -> str:
        """범위 마스킹"""
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return "[N/A]"

        thresholds = config.get("thresholds", {})

        # 기본 임계값
        low = thresholds.get("low", 70)
        target = thresholds.get("target", 90)
        high = thresholds.get("high", 95)

        labels = config.get("labels", {
            "below_low": "Below Threshold",
            "low_to_target": "Below Target",
            "at_target": "At Target",
            "above_target": "Above Target",
            "excellent": "Excellent"
        })

        if num_value < low:
            return labels.get("below_low", "Below Threshold")
        elif num_value < target:
            return labels.get("low_to_target", "Below Target")
        elif num_value < high:
            return labels.get("at_target", "At Target")
        else:
            return labels.get("above_target", "Above Target")

    def _category_mask(self, value: Any, config: dict) -> str:
        """범주화 마스킹"""
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return "N/A"

        bins = config.get("bins", [
            {"max": 50, "label": "LOW"},
            {"max": 80, "label": "MEDIUM"},
            {"max": 100, "label": "HIGH"}
        ])

        for bin_def in bins:
            if num_value <= bin_def.get("max", float("inf")):
                return bin_def.get("label", "UNKNOWN")

        return bins[-1].get("label", "UNKNOWN") if bins else "UNKNOWN"

    def _noise_mask(self, value: Any, config: dict) -> Any:
        """노이즈 추가 마스킹"""
        import random

        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return value

        noise_percent = config.get("noise_percent", 5)
        noise_range = num_value * (noise_percent / 100)
        noise = random.uniform(-noise_range, noise_range)

        result = num_value + noise

        # 소수점 처리
        decimals = config.get("decimals", 2)
        return round(result, decimals)

    # ==================== 편의 메서드 ====================

    def mask_yield_data(self, data: Any, user_role: str) -> Any:
        """수율 데이터 마스킹"""
        return self.mask_data(data, "yield", user_role)

    def mask_equipment_data(self, data: Any, user_role: str) -> Any:
        """장비 데이터 마스킹"""
        return self.mask_data(data, "equipment", user_role)

    def mask_recipe_data(self, data: Any, user_role: str) -> Any:
        """레시피 데이터 마스킹"""
        return self.mask_data(data, "recipe", user_role)

    def mask_sensor_data(self, data: Any, user_role: str) -> Any:
        """센서 데이터 마스킹"""
        return self.mask_data(data, "sensor", user_role)


# ==================== 기본 마스킹 규칙 초기화 ====================

def initialize_default_masking_rules(db: Session):
    """기본 마스킹 규칙 초기화"""
    dms = DataMaskingService(db)

    default_rules = [
        # 파트너사용 수율 데이터 마스킹
        {
            "name": "Partner Yield Masking",
            "resource": "yield",
            "field": "yield_percent",
            "mask_type": "RANGE",
            "mask_config": {
                "thresholds": {"low": 70, "target": 90, "high": 95},
                "labels": {
                    "below_low": "Below Threshold",
                    "low_to_target": "Below Target",
                    "at_target": "At Target",
                    "above_target": "Above Target"
                }
            },
            "applies_to_roles": ["partner"],
            "description": "파트너사에 수율 정확한 수치 대신 범위 표시"
        },
        # 파트너사용 레시피 숨김
        {
            "name": "Partner Recipe Hiding",
            "resource": "wafer",
            "field": "recipe_id",
            "mask_type": "HIDE",
            "mask_config": {"replacement": "[CONFIDENTIAL]"},
            "applies_to_roles": ["partner"],
            "description": "파트너사에 레시피 정보 숨김"
        },
        # 파트너사용 센서 데이터 노이즈
        {
            "name": "Partner Sensor Data Noise",
            "resource": "sensor",
            "field": "temperature",
            "mask_type": "NOISE",
            "mask_config": {"noise_percent": 3, "decimals": 1},
            "applies_to_roles": ["partner"],
            "description": "파트너사에 센서 데이터 약간의 노이즈 추가"
        },
        # 외부 사용자 웨이퍼 ID 해시
        {
            "name": "External Wafer ID Hashing",
            "resource": "wafer",
            "field": "wafer_id",
            "mask_type": "HASH",
            "mask_config": {"salt": "hyspace_wafer_salt"},
            "applies_to_roles": ["external", "partner"],
            "description": "외부 사용자에 웨이퍼 ID 해시 처리"
        },
        # 운영자용 상세 결함 정보 부분 마스킹
        {
            "name": "Operator Defect Detail Partial",
            "resource": "defect",
            "field": "defect_id",
            "mask_type": "PARTIAL",
            "mask_config": {"show_first": 3, "show_last": 2, "mask_char": "*"},
            "applies_to_roles": ["operator"],
            "description": "운영자에 결함 ID 부분 마스킹"
        }
    ]

    for rule_data in default_rules:
        existing = db.query(DataMaskingRule).filter(
            DataMaskingRule.name == rule_data["name"]
        ).first()

        if not existing:
            dms.create_rule(
                name=rule_data["name"],
                resource=rule_data["resource"],
                field=rule_data["field"],
                mask_type=rule_data["mask_type"],
                mask_config=rule_data.get("mask_config"),
                applies_to_roles=rule_data.get("applies_to_roles"),
                description=rule_data.get("description")
            )
