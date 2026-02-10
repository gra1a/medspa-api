"""Cursor-based pagination: cursor + limit, response with next_cursor."""

from typing import Generic, List, Optional, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class PaginationParams(BaseModel):
    """Cursor and limit for list queries. Cursor is the ulid of the last item from the previous page."""

    cursor: Optional[str] = None
    limit: int = DEFAULT_LIMIT


def get_pagination(
    cursor: Optional[str] = Query(None, description="Cursor (ulid of last item from previous page)"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Max items per page"),
) -> PaginationParams:
    """Dependency for cursor + limit query params. Use as Depends(get_pagination)."""
    return PaginationParams(cursor=cursor, limit=limit)


class PaginatedResponse(BaseModel, Generic[T]):
    """Response for cursor-paginated lists: items, next_cursor (if more), limit."""

    items: List[T]
    next_cursor: Optional[str] = None
    limit: int
