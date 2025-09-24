from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db import Base

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String)
    description = Column(Text, nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    category = Column(String, nullable=True)
    security_label = Column(String, nullable=True, index=True)
    security_prob = Column(Float, nullable=True)
    security_sim = Column(Float, nullable=True)
    model_version = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    unique_hash = Column(String, unique=True, index=True)  # Duplicate kontrolü için
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    source = relationship("Source", back_populates="tenders")
