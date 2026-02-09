"""
Tier 1 Pydantic Schemas — 기존 스키마와 직접 연결되는 노드 타입

Foundry, FabSite, ProcessGeneration, MemoryStandard, InterconnectStandard, SubstrateType
"""

from pydantic import BaseModel, Field
from typing import Optional


class FoundrySchema(BaseModel):
    """파운드리 기업"""
    key: str = Field(..., description="Unique key (e.g., TSMC)")
    name: str
    full_name: Optional[str] = None
    country: str
    hq: Optional[str] = None
    founded_year: Optional[int] = None
    fab_count: Optional[int] = None
    revenue_b_usd: Optional[float] = None
    market_share_pct: Optional[float] = None
    employees: Optional[int] = None
    wafer_capacity_kwpm: Optional[int] = None
    description: Optional[str] = None


class FabSiteSchema(BaseModel):
    """팹 사이트"""
    key: str
    name: str
    foundry_key: str = Field(..., description="Parent Foundry key")
    location: str
    wafer_size_mm: int = 300
    capacity_wspm: Optional[int] = None
    status: str = Field("ACTIVE", description="ACTIVE, UNDER_CONSTRUCTION, PLANNED, CLOSED")
    process_nodes: list[str] = Field(default_factory=list, description="Supported ProcessNode keys")
    opened_year: Optional[int] = None
    investment_b_usd: Optional[float] = None
    description: Optional[str] = None


class ProcessGenerationSchema(BaseModel):
    """트랜지스터 세대"""
    key: str
    name: str
    transistor_type: str
    era: Optional[str] = None
    min_node_nm: Optional[float] = None
    description: Optional[str] = None


class MemoryStandardSchema(BaseModel):
    """메모리 규격"""
    key: str
    name: str
    jedec_id: Optional[str] = None
    type: str = Field(..., description="DDR, LPDDR, GDDR, HBM, CXL")
    generation: Optional[int] = None
    max_speed_mtps: Optional[int] = None
    bandwidth_gbps: Optional[float] = None
    voltage_v: Optional[float] = None
    description: Optional[str] = None


class InterconnectStandardSchema(BaseModel):
    """인터커넥트 규격"""
    key: str
    name: str
    version: str
    protocol_type: str = Field(..., description="PCIe, CXL, UCIe, NVLink, InfinityFabric, UALink")
    bandwidth_gtps: Optional[float] = None
    bandwidth_per_lane_gbps: Optional[float] = None
    total_bandwidth_gbps: Optional[float] = None
    year: Optional[int] = None
    description: Optional[str] = None


class SubstrateTypeSchema(BaseModel):
    """패키징 기판 유형"""
    key: str
    name: str
    type: str = Field(..., description="organic, silicon, glass, interconnect_technology")
    line_space_um: Optional[float] = None
    application: Optional[str] = None
    description: Optional[str] = None
