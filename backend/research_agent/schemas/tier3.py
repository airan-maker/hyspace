"""
Tier 3 Pydantic Schemas — 심화 도메인

ReliabilityTest, Standard, Application, ThermalSolution, Regulation, InspectionMethod
"""

from pydantic import BaseModel, Field
from typing import Optional


class ReliabilityTestSchema(BaseModel):
    """신뢰성 시험"""
    key: str
    name: str
    standard: Optional[str] = None
    type: str = Field(..., description="HTOL, TC, ESD, EM, TDDB, AUTOMOTIVE")
    duration_hours: Optional[int] = None
    temperature_c: Optional[float] = None
    conditions: Optional[str] = None
    description: Optional[str] = None


class StandardSchema(BaseModel):
    """산업 표준"""
    key: str
    name: str
    org: str = Field(..., description="JEDEC, IEEE, SEMI, AEC")
    version: Optional[str] = None
    year: Optional[int] = None
    scope: Optional[str] = None
    description: Optional[str] = None


class ApplicationSchema(BaseModel):
    """응용 분야"""
    key: str
    name: str
    segment: str = Field(..., description="DATACENTER, EDGE, MOBILE, AUTOMOTIVE")
    workload: Optional[str] = None
    requirements: Optional[dict] = None
    description: Optional[str] = None


class ThermalSolutionSchema(BaseModel):
    """열 관리 솔루션"""
    key: str
    name: str
    type: str = Field(..., description="AIR, LIQUID, IMMERSION")
    max_tdp_w: Optional[int] = None
    thermal_resistance_c_per_w: Optional[float] = None
    description: Optional[str] = None


class RegulationSchema(BaseModel):
    """규제/정책"""
    key: str
    name: str
    jurisdiction: str
    type: str = Field(..., description="EXPORT_CONTROL, SUBSIDY, ENVIRONMENTAL")
    effective_year: Optional[int] = None
    impact: Optional[str] = None
    description: Optional[str] = None


class InspectionMethodSchema(BaseModel):
    """검사/계측 방법"""
    key: str
    name: str
    equipment_type: Optional[str] = None
    vendor: Optional[str] = None
    resolution_nm: Optional[float] = None
    throughput: Optional[str] = None
    detection_capability: Optional[str] = None
    description: Optional[str] = None
