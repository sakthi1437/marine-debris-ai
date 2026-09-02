from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, String
from backend.database.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True)
    survey_id = Column(String, index=True, nullable=False)
    image_name = Column(String, nullable=False)
    object_type = Column(String, nullable=False)
    model_confidence = Column(Float, nullable=False)
    final_confidence = Column(Float, nullable=False)
    priority = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    metadata_source = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
