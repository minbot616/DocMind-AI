import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from utils import logger

# Base class for declarative ORM models
Base = declarative_base()

import sys

PROD_DB_NAME = "docmind_db"

def assert_not_production_db(target_url: str):
    """Production Guard: Refuses test execution if target_url points to the production database."""
    if os.getenv("TESTING") == "true" or "pytest" in sys.modules:
        url_lower = (target_url or "").lower()
        if PROD_DB_NAME in url_lower and "test" not in url_lower:
            raise RuntimeError("Refusing to run tests against the production database.")

def get_engine(url: str = None):
    """Initializes SQLAlchemy Engine for production PostgreSQL or isolated test configuration."""
    db_url = url or os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/docmind_db"
    assert_not_production_db(db_url)
    
    if db_url.startswith("sqlite"):
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
    try:
        eng = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5}
        )

        # Test connection immediately to verify PostgreSQL availability
        with eng.connect() as conn:
            pass
        return eng
    except Exception as e:
        logger.error(f"PostgreSQL connection error: {e}")
        raise RuntimeError("PostgreSQL database is unavailable. Please verify connection credentials and ensure PostgreSQL service is running.") from e


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager supplying a transactional SQLAlchemy DB session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
