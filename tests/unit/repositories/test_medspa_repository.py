import pytest
from sqlalchemy.orm import Session

pytestmark = pytest.mark.unit

from app.models.models import Medspa
from app.repositories.medspa_repository import MedspaRepository
from app.utils.ulid import generate_ulid


def test_get_by_id_found(db_session: Session, sample_medspa: Medspa):
    got = MedspaRepository.get_by_id(db_session, sample_medspa.id)
    assert got is not None
    assert got.id == sample_medspa.id
    assert got.ulid == sample_medspa.ulid
    assert got.name == sample_medspa.name


def test_get_by_id_not_found(db_session: Session):
    assert MedspaRepository.get_by_id(db_session, 99999) is None


def test_get_by_ulid_found(db_session: Session, sample_medspa: Medspa):
    got = MedspaRepository.get_by_ulid(db_session, sample_medspa.ulid)
    assert got is not None
    assert got.id == sample_medspa.id
    assert got.ulid == sample_medspa.ulid


def test_get_by_ulid_not_found(db_session: Session):
    assert MedspaRepository.get_by_ulid(db_session, generate_ulid()) is None


def test_list_all_empty(db_session: Session):
    assert MedspaRepository.list_all(db_session) == []


def test_list_all_returns_ordered(db_session: Session, sample_medspa: Medspa):
    medspas = MedspaRepository.list_all(db_session)
    assert len(medspas) >= 1
    assert medspas[0].id == sample_medspa.id
    ids = [m.id for m in medspas]
    assert ids == sorted(ids)


def test_add_persists_and_returns_medspa(db_session: Session):
    medspa = Medspa(
        ulid=generate_ulid(),
        name="New MedSpa",
        address="456 St",
        phone_number=None,
        email=None,
    )
    added = MedspaRepository.persist_new(db_session, medspa)
    assert added.id is not None
    assert added.name == "New MedSpa"
    got = MedspaRepository.get_by_ulid(db_session, added.ulid)
    assert got is not None
    assert got.name == added.name


def test_upsert_by_ulid_inserts_when_not_found(db_session: Session):
    ulid = generate_ulid()
    medspa = Medspa(ulid=ulid, name="Upsert New", address="1 St", phone_number="111", email="a@b.com")
    result = MedspaRepository.upsert_by_ulid(db_session, medspa)
    assert result.id is not None
    assert result.ulid == ulid
    assert result.name == "Upsert New"
    assert MedspaRepository.get_by_ulid(db_session, ulid).name == "Upsert New"


def test_upsert_by_ulid_updates_when_found(db_session: Session, sample_medspa: Medspa):
    ulid = sample_medspa.ulid
    updated = Medspa(
        ulid=ulid,
        name="Updated Name",
        address="New Address",
        phone_number="999",
        email="new@example.com",
    )
    result = MedspaRepository.upsert_by_ulid(db_session, updated)
    assert result.id == sample_medspa.id
    assert result.ulid == ulid
    assert result.name == "Updated Name"
    assert result.address == "New Address"
    assert result.phone_number == "999"
    assert result.email == "new@example.com"
    got = MedspaRepository.get_by_ulid(db_session, ulid)
    assert got.name == "Updated Name"
