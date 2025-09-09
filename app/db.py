from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import settings

Base = declarative_base()


engine = create_engine(
	settings.DATABASE_URL,
	connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
