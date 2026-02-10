from typing import Type, TypeVar

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError

T = TypeVar("T")


def get_by_ulid(
    db: Session,
    model: Type[T],
    ulid: str,
    not_found_message: str = "Not found",
) -> T:
    """Load a single row by ulid."""
    entity = db.query(model).filter(model.ulid == ulid).first()
    if not entity:
        raise NotFoundError(not_found_message)
    return entity
