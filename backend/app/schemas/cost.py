from pydantic import BaseModel, Field
from typing import Optional


class CostRequest(BaseModel):
    """비용 계산 요청"""
    die_size_mm2: float = Field(..., gt=0, description="다이 면적 (mm²)")
    process_node_nm: int = Field(..., ge=3, le=14, description="공정 노드 (nm)")
    volume: int = Field(default=100000, ge=1000, description="연간 생산량")
    target_asp: float = Field(default=100.0, gt=0, description="목표 판매가 (USD)")

    class Config:
        json_schema_extra = {
            "example": {
                "die_size_mm2": 127.5,
                "process_node_nm": 5,
                "volume": 100000,
                "target_asp": 89.0
            }
        }


class CostResponse(BaseModel):
    """비용 계산 결과"""
    wafer_cost: float = Field(..., description="웨이퍼 비용 (USD)")
    die_cost: float = Field(..., description="다이 비용 (USD)")
    good_die_cost: float = Field(..., description="양품 다이 비용 (USD)")
    package_cost: float = Field(..., description="패키징 비용 (USD)")
    test_cost: float = Field(..., description="테스트 비용 (USD)")
    total_unit_cost: float = Field(..., description="총 단위 비용 (USD)")
    target_asp: float = Field(..., description="목표 판매가 (USD)")
    gross_margin: float = Field(..., description="매출 총이익 (USD)")
    gross_margin_percent: float = Field(..., description="매출 총이익률 (%)")
    net_die_per_wafer: int = Field(..., description="웨이퍼당 양품 다이 수")
    yield_rate: float = Field(..., description="수율 (%)")

    class Config:
        json_schema_extra = {
            "example": {
                "wafer_cost": 16000.0,
                "die_cost": 30.53,
                "good_die_cost": 39.14,
                "package_cost": 8.50,
                "test_cost": 2.20,
                "total_unit_cost": 49.84,
                "target_asp": 89.0,
                "gross_margin": 39.16,
                "gross_margin_percent": 44.0,
                "net_die_per_wafer": 524,
                "yield_rate": 78.5
            }
        }


class VolumeEconomicsItem(BaseModel):
    """볼륨별 경제성 항목"""
    volume: int
    unit_cost: float
    total_cost: float
    volume_discount: float
    break_even_volume: int


class VolumeAnalysisRequest(BaseModel):
    """볼륨 분석 요청"""
    die_size_mm2: float = Field(..., gt=0)
    process_node_nm: int = Field(..., ge=3, le=14)
    target_asp: float = Field(default=100.0, gt=0)
    volumes: list[int] = Field(default=[10000, 50000, 100000, 500000, 1000000])


class VolumeAnalysisResponse(BaseModel):
    """볼륨 분석 결과"""
    analysis: list[VolumeEconomicsItem]
