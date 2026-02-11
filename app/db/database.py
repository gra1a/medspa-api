import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@contextmanager
def transaction(session: Session) -> Generator[Session, None, None]:
    """Context manager for service-layer transactions. Commits on success, rolls back on exception."""
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("transaction rollback")
        raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all():
    """Create all tables (e.g. for test database)."""
    Base.metadata.create_all(bind=engine)
