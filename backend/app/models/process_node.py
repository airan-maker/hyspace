from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from ..database import Base


class ProcessNode(Base):
    __tablename__ = "process_nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)  # "3nm", "5nm", "7nm"
    node_nm = Column(Integer, nullable=False)  # 3, 5, 7
    wafer_cost = Column(Float, nullable=False)  # USD per wafer
    defect_density = Column(Float, nullable=False)  # defects per cm²
    base_core_area = Column(Float, nullable=False)  # mm² per CPU core
    cache_density = Column(Float, nullable=False)  # mm² per MB of cache
    io_area_per_lane = Column(Float, nullable=False)  # mm² per PCIe lane
    scaling_factor = Column(Float, default=1.0)  # area scaling factor
    power_density = Column(Float, nullable=False)  # mW per mm²
    max_frequency_ghz = Column(Float, nullable=False)  # max clock frequency
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
