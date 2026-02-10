import pytest
from sqlalchemy.orm import Session

pytestmark = pytest.mark.unit

from app.exceptions import NotFoundError
from app.models.models import Medspa
from app.utils.query import get_by_id
from app.utils.ulid import generate_id


def test_get_by_id_found(db_session: Session, sample_medspa: Medspa):
    result = get_by_id(db_session, Medspa, sample_medspa.id)
    assert result is not None
    assert result.id == sample_medspa.id


def test_get_by_id_not_found_raises(db_session: Session):
    with pytest.raises(NotFoundError, match="Not found"):
        get_by_id(db_session, Medspa, generate_id())


def test_get_by_id_custom_message(db_session: Session):
    with pytest.raises(NotFoundError, match="Medspa missing"):
        get_by_id(db_session, Medspa, generate_id(), not_found_message="Medspa missing")
