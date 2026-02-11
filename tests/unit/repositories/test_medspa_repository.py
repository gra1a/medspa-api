import pytest
from sqlalchemy.orm import Session

from app.models.models import Medspa
from app.repositories.medspa_repository import MedspaRepository
from app.utils.ulid import generate_id

pytestmark = pytest.mark.unit


def test_list_empty(db_session: Session):
    assert MedspaRepository.list(db_session, limit=10) == []


def test_list_returns_ordered(db_session: Session, sample_medspa: Medspa):
    medspas = MedspaRepository.list(db_session, limit=100)
    assert len(medspas) >= 1
    ids = [m.id for m in medspas]
    assert ids == sorted(ids)


def test_list_respects_limit(db_session: Session, multiple_medspas):
    # Repository returns up to limit+1 to detect "has next page"
    raw = MedspaRepository.list(db_session, limit=2)
    assert len(raw) == 3  # 2 requested + 1 extra
    ids = [m.id for m in raw]
    assert ids == sorted(ids)


def test_list_with_cursor_returns_only_after_cursor(db_session: Session, multiple_medspas):
    all_ordered = MedspaRepository.list(db_session, limit=10)
    assert len(all_ordered) >= 3
    ids = [m.id for m in all_ordered]
    cursor = ids[1]  # after second item
    page = MedspaRepository.list(db_session, cursor=cursor, limit=10)
    page_ids = [m.id for m in page]
    assert all(u > cursor for u in page_ids)
    assert ids[2] == page_ids[0]


def test_add_persists_and_returns_medspa(db_session: Session):
    medspa = Medspa(
        id=generate_id(),
        name="New MedSpa",
        address="456 St",
        phone_number="(512) 555-0199",
        email="new@medspa.com",
    )
    added = MedspaRepository.create(db_session, medspa)
    assert added.id is not None
    assert added.name == "New MedSpa"
    db_session.commit()
    got = db_session.get(Medspa, added.id)
    assert got is not None
    assert got.name == added.name
