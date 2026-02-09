"""
Tier 2 Pydantic Schemas — 산업 생태계 확장

EquipmentVendor, EquipmentModel, MaterialSupplier, DesignIP, Company, Benchmark
"""

from pydantic import BaseModel, Field
from typing import Optional


class EquipmentVendorSchema(BaseModel):
    """장비 벤더"""
    key: str
    name: str
    country: str
    hq: Optional[str] = None
    revenue_b_usd: Optional[float] = None
    market_segment: Optional[str] = None
    founded_year: Optional[int] = None
    employees: Optional[int] = None
    description: Optional[str] = None


class EquipmentModelSchema(BaseModel):
    """장비 모델"""
    key: str
    name: str
    vendor_key: str
    category: str = Field(..., description="LITHOGRAPHY, ETCH, DEPOSITION, CMP, INSPECTION, METROLOGY")
    generation: Optional[str] = None
    min_node_nm: Optional[int] = None
    throughput_wph: Optional[int] = None
    price_m_usd: Optional[float] = None
    description: Optional[str] = None


class MaterialSupplierSchema(BaseModel):
    """소재 공급사"""
    key: str
    name: str
    country: str
    specialization: Optional[str] = None
    market_share_pct: Optional[float] = None
    revenue_b_usd: Optional[float] = None
    description: Optional[str] = None


class DesignIPSchema(BaseModel):
    """설계 IP"""
    key: str
    name: str
    vendor: str
    type: str = Field(..., description="CPU_CORE, GPU_CORE, NPU, PHY, SERDES")
    architecture: Optional[str] = None
    description: Optional[str] = None


class CompanySchema(BaseModel):
    """반도체 기업"""
    key: str
    name: str
    type: str = Field(..., description="FABLESS, IDM, FOUNDRY, OSAT")
    country: str
    hq: Optional[str] = None
    revenue_b_usd: Optional[float] = None
    market_cap_b_usd: Optional[float] = None
    focus: list[str] = Field(default_factory=list)
    founded_year: Optional[int] = None
    description: Optional[str] = None


class BenchmarkSchema(BaseModel):
    """벤치마크"""
    key: str
    name: str
    category: str = Field(..., description="MLPERF, EFFICIENCY, BANDWIDTH, SPEC")
    metric_unit: str
    higher_is_better: bool = True
    org: Optional[str] = None
    description: Optional[str] = None
