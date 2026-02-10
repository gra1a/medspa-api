from functools import wraps
from typing import Any, Callable, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

F = TypeVar("F", bound=Callable[..., Any])


def transaction(f: F) -> F:
    """Decorator for repository methods: commits on success, rolls back on exception. Session must be the first positional arg (db)."""
    @wraps(f)
    def wrap(*args: Any, **kwargs: Any) -> Any:
        db = args[0] if args else kwargs.get("db")
        if not isinstance(db, Session):
            raise TypeError("@transaction requires Session as first argument (db)")
        try:
            result = f(*args, **kwargs)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise
    return wrap  # type: ignore[return-value]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all():
    """Create all tables (e.g. for test database)."""
    Base.metadata.create_all(bind=engine)
