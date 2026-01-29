from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from .ppa import ChipConfigRequest, PPAResponse, AreaBreakdown, PowerBreakdown
from .cost import CostResponse


class FullSimulationRequest(BaseModel):
    """통합 시뮬레이션 요청 (PPA + 비용)"""
    name: Optional[str] = Field(default=None, description="시뮬레이션 이름")
    config: ChipConfigRequest
    volume: int = Field(default=100000, ge=1000, description="연간 생산량")
    target_asp: float = Field(default=100.0, gt=0, description="목표 판매가 (USD)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "AI Accelerator v1",
                "config": {
                    "process_node_nm": 5,
                    "cpu_cores": 8,
                    "gpu_cores": 16,
                    "npu_cores": 8,
                    "l2_cache_mb": 8,
                    "l3_cache_mb": 64,
                    "pcie_lanes": 32,
                    "memory_channels": 4,
                    "target_frequency_ghz": 3.2
                },
                "volume": 100000,
                "target_asp": 150.0
            }
        }


class FullSimulationResponse(BaseModel):
    """통합 시뮬레이션 결과"""
    id: UUID
    name: Optional[str]
    config: ChipConfigRequest
    ppa: PPAResponse
    cost: CostResponse
    confidence_score: float
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "AI Accelerator v1",
                "config": {
                    "process_node_nm": 5,
                    "cpu_cores": 8,
                    "gpu_cores": 16,
                    "npu_cores": 8,
                    "l2_cache_mb": 8,
                    "l3_cache_mb": 64,
                    "pcie_lanes": 32,
                    "memory_channels": 4,
                    "target_frequency_ghz": 3.2
                },
                "ppa": {
                    "die_size_mm2": 127.5,
                    "power_tdp_w": 85.0,
                    "performance_ghz": 3.2,
                    "performance_tops": 64.0,
                    "efficiency_tops_per_watt": 0.75,
                    "confidence_score": 90,
                    "area_breakdown": {},
                    "power_breakdown": {}
                },
                "cost": {
                    "wafer_cost": 16000.0,
                    "die_cost": 30.53,
                    "good_die_cost": 39.14,
                    "package_cost": 12.0,
                    "test_cost": 3.5,
                    "total_unit_cost": 54.64,
                    "target_asp": 150.0,
                    "gross_margin": 95.36,
                    "gross_margin_percent": 63.6,
                    "net_die_per_wafer": 524,
                    "yield_rate": 78.5
                },
                "confidence_score": 90,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class SimulationSummary(BaseModel):
    """시뮬레이션 요약 (목록 조회용)"""
    id: UUID
    name: Optional[str]
    process_node_nm: int
    die_size_mm2: float
    power_tdp_w: float
    total_unit_cost: float
    gross_margin_percent: float
    confidence_score: float
    created_at: datetime
