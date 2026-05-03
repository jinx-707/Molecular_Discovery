"""
Sync SQLAlchemy session — uses psycopg2 driver.
Falls back gracefully when Postgres is unavailable (SQLite for demo).
"""
import os
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/moldiscovery",
)

# ---------------------------------------------------------------------------
# Try Postgres; fall back to SQLite so the app starts without a DB server
# ---------------------------------------------------------------------------

def _make_engine():
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={})
        # Quick connectivity check
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("Connected to PostgreSQL: %s", DATABASE_URL)
        return engine
    except Exception as exc:
        log.warning("PostgreSQL unavailable (%s) — falling back to SQLite", exc)
        sqlite_url = "sqlite:///./moldiscovery_demo.db"
        return create_engine(sqlite_url, connect_args={"check_same_thread": False})


engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables (idempotent)."""
    from app.db.models import Base
    Base.metadata.create_all(bind=engine)
    log.info("Database tables created / verified.")
