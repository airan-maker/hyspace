from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProcessNodeResponse(BaseModel):
    """공정 노드 정보"""
    id: int
    name: str
    node_nm: int
    wafer_cost: float
    defect_density: float
    base_core_area: float
    cache_density: float
    io_area_per_lane: float
    power_density: float
    max_frequency_ghz: float
    is_active: bool

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "5nm",
                "node_nm": 5,
                "wafer_cost": 16000.0,
                "defect_density": 0.08,
                "base_core_area": 0.65,
                "cache_density": 0.45,
                "io_area_per_lane": 0.30,
                "power_density": 0.40,
                "max_frequency_ghz": 3.5,
                "is_active": True
            }
        }


class IPBlockResponse(BaseModel):
    """IP 블록 정보"""
    id: int
    name: str
    type: str
    vendor: Optional[str]
    version: Optional[str]
    area_mm2: float
    power_mw: float
    performance_metric: Optional[float]
    performance_unit: Optional[str]
    silicon_proven: bool
    compatible_nodes: Optional[list[int]]
    description: Optional[str]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Cortex-A78",
                "type": "CPU",
                "vendor": "ARM",
                "version": "r1p0",
                "area_mm2": 0.65,
                "power_mw": 750,
                "performance_metric": 3.0,
                "performance_unit": "GHz",
                "silicon_proven": True,
                "compatible_nodes": [3, 5, 7],
                "description": "High-performance CPU core"
            }
        }
