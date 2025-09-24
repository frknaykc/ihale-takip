from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc
from datetime import datetime
import hashlib
from . import models
from .models import User
from .utils import get_password_hash


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
    security_label: str | None = None,
    security_prob: float | None = None,
    security_sim: float | None = None,
    model_version: str | None = None,
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
        security_label=security_label,
        security_prob=security_prob,
        security_sim=security_sim,
        model_version=model_version,
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
	return results


# User CRUD operations
def get_user(db: Session, user_id: int) -> User | None:
	"""Get user by ID."""
	return db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


def get_user_by_username(db: Session, username: str) -> User | None:
	"""Get user by username."""
	return db.execute(select(User).where(User.username == username)).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> User | None:
	"""Get user by email."""
	return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
	"""Get list of users."""
	return db.execute(select(User).offset(skip).limit(limit)).scalars().all()


def create_user(db: Session, user_data: dict) -> User:
	"""Create a new user."""
	hashed_password = get_password_hash(user_data["password"])
	db_user = User(
		username=user_data["username"],
		email=user_data["email"],
		hashed_password=hashed_password,
		full_name=user_data.get("full_name"),
		is_active=user_data.get("is_active", True),
		is_admin=user_data.get("is_admin", False)
	)
	db.add(db_user)
	db.commit()
	db.refresh(db_user)
	return db_user


def update_user(db: Session, user_id: int, user_data: dict) -> User | None:
	"""Update user information."""
	db_user = get_user(db, user_id)
	if not db_user:
		return None
	
	for field, value in user_data.items():
		if field == "password" and value:
			db_user.hashed_password = get_password_hash(value)
		elif hasattr(db_user, field):
			setattr(db_user, field, value)
	
	db.commit()
	db.refresh(db_user)
	return db_user


def delete_user(db: Session, user_id: int) -> bool:
	"""Delete a user."""
	db_user = get_user(db, user_id)
	if not db_user:
		return False
	
	db.delete(db_user)
	db.commit()
	return True
