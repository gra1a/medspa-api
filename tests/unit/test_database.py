import pytest

from app.db.database import get_db

pytestmark = pytest.mark.unit


def test_get_db_generator_produces_session_and_closes():
    gen = get_db()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass
