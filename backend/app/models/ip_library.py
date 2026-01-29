from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ARRAY
from sqlalchemy.sql import func
from ..database import Base


class IPBlock(Base):
    __tablename__ = "ip_library"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # "CPU", "GPU", "NPU", "MEMORY_CTRL", "SERDES"
    vendor = Column(String(100))
    version = Column(String(50))
    area_mm2 = Column(Float, nullable=False)  # area in mm²
    power_mw = Column(Float, nullable=False)  # power in mW
    performance_metric = Column(Float)  # TOPS for NPU, GFLOPS for GPU, etc.
    performance_unit = Column(String(50))  # "TOPS", "GFLOPS", "GHz"
    silicon_proven = Column(Boolean, default=False)
    compatible_nodes = Column(ARRAY(Integer))  # list of compatible process node IDs
    description = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
