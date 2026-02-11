from typing import TypeVar

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError

T = TypeVar("T")


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
