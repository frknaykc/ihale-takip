from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import settings

Base = declarative_base()


engine = create_engine(
	settings.DATABASE_URL,
	connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _run_startup_migrations():
    statements = [
        "ALTER TABLE tenders ADD COLUMN security_label TEXT",
        "ALTER TABLE tenders ADD COLUMN security_prob REAL",
        "ALTER TABLE tenders ADD COLUMN security_sim REAL",
        "ALTER TABLE tenders ADD COLUMN model_version TEXT",
    ]
    with engine.connect() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except Exception:
                # muhtemelen sütun zaten var
                conn.rollback()
            else:
                conn.commit()


_run_startup_migrations()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
