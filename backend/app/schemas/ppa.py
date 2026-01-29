from pydantic import BaseModel, Field
from typing import Optional


class ChipConfigRequest(BaseModel):
    """칩 구성 요청 스키마"""
    process_node_nm: int = Field(..., ge=3, le=14, description="공정 노드 (nm)")
    cpu_cores: int = Field(..., ge=1, le=128, description="CPU 코어 수")
    gpu_cores: int = Field(default=0, ge=0, le=256, description="GPU 코어 수")
    npu_cores: int = Field(default=0, ge=0, le=64, description="NPU 코어 수")
    l2_cache_mb: float = Field(default=4.0, ge=0.5, le=64, description="L2 캐시 (MB)")
    l3_cache_mb: float = Field(default=0, ge=0, le=512, description="L3 캐시 (MB)")
    pcie_lanes: int = Field(default=16, ge=0, le=128, description="PCIe 레인 수")
    memory_channels: int = Field(default=2, ge=1, le=16, description="메모리 채널 수")
    target_frequency_ghz: float = Field(default=3.0, ge=1.0, le=6.0, description="목표 주파수 (GHz)")

    class Config:
        json_schema_extra = {
            "example": {
                "process_node_nm": 5,
                "cpu_cores": 8,
                "gpu_cores": 16,
                "npu_cores": 4,
                "l2_cache_mb": 8,
                "l3_cache_mb": 32,
                "pcie_lanes": 24,
                "memory_channels": 4,
                "target_frequency_ghz": 3.2
            }
        }


class AreaBreakdown(BaseModel):
    """면적 상세 내역"""
    cpu: float
    gpu: float
    npu: float
    l2_cache: float
    l3_cache: float
    io: float
    memory_controller: float
    overhead: float
    total: float


class PowerBreakdown(BaseModel):
    """전력 상세 내역"""
    cpu: float
    gpu: float
    npu: float
    cache: float
    io: float
    total: float


class PPAResponse(BaseModel):
    """PPA 계산 결과"""
    die_size_mm2: float = Field(..., description="다이 면적 (mm²)")
    power_tdp_w: float = Field(..., description="TDP (W)")
    performance_ghz: float = Field(..., description="동작 주파수 (GHz)")
    performance_tops: float = Field(..., description="AI 연산 성능 (TOPS)")
    efficiency_tops_per_watt: float = Field(..., description="전력 효율 (TOPS/W)")
    confidence_score: float = Field(..., description="신뢰도 점수 (0-100)")
    area_breakdown: AreaBreakdown
    power_breakdown: PowerBreakdown

    class Config:
        json_schema_extra = {
            "example": {
                "die_size_mm2": 127.5,
                "power_tdp_w": 45.2,
                "performance_ghz": 3.2,
                "performance_tops": 32.0,
                "efficiency_tops_per_watt": 0.708,
                "confidence_score": 90,
                "area_breakdown": {
                    "cpu": 5.2,
                    "gpu": 3.2,
                    "npu": 1.12,
                    "l2_cache": 3.6,
                    "l3_cache": 14.4,
                    "io": 7.2,
                    "memory_controller": 12.0,
                    "overhead": 7.0,
                    "total": 127.5
                },
                "power_breakdown": {
                    "cpu": 25.6,
                    "gpu": 9.6,
                    "npu": 0.8,
                    "cache": 2.0,
                    "io": 7.2,
                    "total": 45.2
                }
            }
        }


class PPAAlternativeItem(BaseModel):
    """대안 구성 항목"""
    variant: str = Field(..., description="구성 유형 (current, low_power, high_performance)")
    result: PPAResponse


class PPAAlternativesResponse(BaseModel):
    """대안 구성 비교 결과"""
    alternatives: list[PPAAlternativeItem]
