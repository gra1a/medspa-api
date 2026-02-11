import pytest
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.models import Medspa
from app.schemas.medspas import MedspaCreate
from app.services.medspa_service import MedspaService
from app.utils.ulid import generate_id

pytestmark = pytest.mark.unit


def test_get_medspa_found(db_session: Session, sample_medspa: Medspa):
    got = MedspaService.get_medspa(db_session, sample_medspa.id)
    assert got.id == sample_medspa.id
    assert got.name == sample_medspa.name


def test_get_medspa_not_found(db_session: Session):
    with pytest.raises(NotFoundError, match="Medspa not found"):
        MedspaService.get_medspa(db_session, generate_id())


def test_list_medspas_empty(db_session: Session):
    items, next_cursor = MedspaService.list_medspas(db_session, limit=20)
    assert isinstance(items, list)
    assert next_cursor is None


def test_list_medspas_returns_all(db_session: Session, sample_medspa: Medspa):
    items, next_cursor = MedspaService.list_medspas(db_session, limit=20)
    assert len(items) >= 1
    ids = [m.id for m in items]
    assert sample_medspa.id in ids


def test_list_medspas_next_cursor_set_when_more_results(db_session: Session, multiple_medspas):
    items, next_cursor = MedspaService.list_medspas(db_session, limit=2)
    assert len(items) == 2
    assert next_cursor is not None
    assert next_cursor == items[1].id


def test_list_medspas_next_cursor_none_when_no_more(db_session: Session, sample_medspa: Medspa):
    items, next_cursor = MedspaService.list_medspas(db_session, limit=20)
    assert len(items) >= 1
    assert next_cursor is None


def test_list_medspas_cursor_pagination_no_duplicates(db_session: Session, multiple_medspas):
    page1, next_cursor = MedspaService.list_medspas(db_session, limit=2)
    assert len(page1) == 2
    assert next_cursor is not None
    page2, next_cursor2 = MedspaService.list_medspas(db_session, cursor=next_cursor, limit=2)
    assert len(page2) == 2
    page1_ids = {m.id for m in page1}
    page2_ids = {m.id for m in page2}
    assert page1_ids.isdisjoint(page2_ids)
    assert next_cursor2 is not None
    page3, next_cursor3 = MedspaService.list_medspas(db_session, cursor=next_cursor2, limit=2)
    assert len(page3) == 1
    assert next_cursor3 is None
    all_ids = page1_ids | page2_ids | {m.id for m in page3}
    assert len(all_ids) == 5


def test_create_medspa_success(db_session: Session):
    data = MedspaCreate(
        name="New MedSpa",
        address="100 Main St",
        phone_number="555-1234",
        email="contact@example.com",
    )
    medspa = MedspaService.create_medspa(db_session, data)
    assert medspa.id is not None
    assert medspa.name == "New MedSpa"
    assert medspa.address == "100 Main St"
    got = MedspaService.get_medspa(db_session, medspa.id)
    assert got.name == medspa.name
