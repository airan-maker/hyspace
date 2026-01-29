from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..database import Base


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200))
    config = Column(JSON, nullable=False)  # input parameters
    result = Column(JSON, nullable=False)  # calculation results
    confidence_score = Column(Float)  # 0-100
    created_at = Column(DateTime(timezone=True), server_default=func.now())
