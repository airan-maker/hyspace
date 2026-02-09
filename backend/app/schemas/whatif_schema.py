"""
What-If Simulation Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ScenarioType(str, Enum):
    EQUIPMENT_DELAY = "equipment_delay"
    MATERIAL_SHORTAGE = "material_shortage"
    PROCESS_DELAY = "process_delay"


class WhatIfRequest(BaseModel):
    scenario_type: ScenarioType
    target_entity: str = Field(..., description="영향 대상 엔티티 이름 (예: ASML, EUV Photoresist)")
    delay_months: int = Field(default=3, ge=1, le=24, description="지연/중단 기간 (개월)")
    include_ai_narrative: bool = Field(default=True, description="AI 내러티브 포함 여부")


class AffectedNode(BaseModel):
    id: int
    label: str
    name: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    impact_reason: str


class WhatIfResponse(BaseModel):
    scenario: dict
    affected_nodes: list[AffectedNode]
    affected_node_ids: list[int]
    total_affected: int
    alternatives: list[dict] = []
    narrative: Optional[str] = None


class WhatIfPreset(BaseModel):
    id: str
    label: str
    description: str
    scenario_type: ScenarioType
    target_entity: str
    delay_months: int
