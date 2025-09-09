from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class Source(Base):
	__tablename__ = "sources"

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String(255), nullable=False)
	url = Column(String(1000), nullable=False, unique=True)
	slug = Column(String(100), nullable=False, unique=True)

	tenders = relationship("Tender", back_populates="source")


class Tender(Base):
	__tablename__ = "tenders"
	__table_args__ = (
		UniqueConstraint("unique_hash", name="uq_tenders_unique_hash"),
	)

	id = Column(Integer, primary_key=True, index=True)
	source_id = Column(ForeignKey("sources.id"), nullable=False, index=True)
	title = Column(String(1000), nullable=False)
	url = Column(String(2000), nullable=False)
	description = Column(Text, nullable=True)
	published_at = Column(DateTime, nullable=True)
	unique_hash = Column(String(64), nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

	source = relationship("Source", back_populates="tenders")
