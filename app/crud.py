from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc
from datetime import datetime
import hashlib
from . import models


def ensure_source(db: Session, name: str, url: str, slug: str) -> models.Source:
	existing = db.execute(select(models.Source).where(models.Source.slug == slug)).scalar_one_or_none()
	if existing:
		return existing
	source = models.Source(name=name, url=url, slug=slug)
	db.add(source)
	db.commit()
	db.refresh(source)
	return source


def compute_tender_hash(title: str, url: str, published_at: datetime | None) -> str:
	to_hash = f"{title}|{url}|{published_at.isoformat() if published_at else ''}"
	return hashlib.sha256(to_hash.encode("utf-8")).hexdigest()


def create_tender_if_new(
	db: Session,
	source: models.Source,
	title: str,
	url: str,
	description: str | None = None,
	published_at: datetime | None = None,
) -> models.Tender | None:
	unique_hash = compute_tender_hash(title, url, published_at)
	existing = db.execute(
		select(models.Tender).where(models.Tender.unique_hash == unique_hash)
	).scalar_one_or_none()
	if existing:
		return None
	tender = models.Tender(
		source_id=source.id,
		title=title.strip(),
		url=url.strip(),
		description=(description or "").strip() or None,
		published_at=published_at,
		unique_hash=unique_hash,
	)
	db.add(tender)
	db.commit()
	db.refresh(tender)
	return tender


def filter_tenders(
	db: Session,
	query: str | None,
	source_slug: str | None,
	date_from: datetime | None,
	date_to: datetime | None,
	limit: int,
	offset: int,
	category: str | None = None,
):
	from sqlalchemy.orm import joinedload
	stmt = select(models.Tender).options(joinedload(models.Tender.source))
	conditions = []
	
	if query:
		q = f"%{query.lower()}%"
		conditions.append(or_(
			func.lower(models.Tender.title).like(q),
			func.lower(models.Tender.description).like(q),
		))
	
	if source_slug:
		stmt = stmt.join(models.Source)
		conditions.append(models.Source.slug == source_slug)
	
	if date_from:
		conditions.append(models.Tender.published_at >= date_from)
	if date_to:
		conditions.append(models.Tender.published_at <= date_to)
	
	if conditions:
		stmt = stmt.where(and_(*conditions))
	
	stmt = stmt.order_by(desc(models.Tender.published_at), desc(models.Tender.id)).limit(limit).offset(offset)
	results = db.execute(stmt).scalars().all()

	# Kategori filtresi
	if category:
		from .lib.categories import classifyTender
		results = [tender for tender in results if classifyTender(tender.title, tender.description or "") == category]
	
	return results
