from typing import Any, Protocol, TypeVar

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError


class HasIdColumn(Protocol):
    """Protocol for ORM models with an id column (used for get_by_id)."""

    id: Any  # Column descriptor; comparison with str yields a SQL expression


T = TypeVar("T", bound=HasIdColumn)


def get_by_id(
    db: Session,
    model: type[T],
    id: str,
    not_found_message: str = "Not found",
) -> T:
    """Load a single row by id."""
    entity = db.query(model).filter(model.id == id).first()
    if not entity:
        raise NotFoundError(not_found_message)
    return entity
