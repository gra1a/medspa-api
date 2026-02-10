import pytest
from sqlalchemy.orm import Session

pytestmark = pytest.mark.unit

from app.models.models import Service
from app.repositories.service_repository import ServiceRepository
from app.utils.ulid import generate_ulid


def test_get_by_id_found(db_session: Session, sample_service: Service):
    got = ServiceRepository.get_by_id(db_session, sample_service.id)
    assert got is not None
    assert got.id == sample_service.id
    assert got.ulid == sample_service.ulid
    assert got.name == sample_service.name


def test_get_by_id_not_found(db_session: Session):
    assert ServiceRepository.get_by_id(db_session, 99999) is None


def test_get_by_ulid_found(db_session: Session, sample_service: Service):
    got = ServiceRepository.get_by_ulid(db_session, sample_service.ulid)
    assert got is not None
    assert got.id == sample_service.id


def test_get_by_ulid_not_found(db_session: Session):
    assert ServiceRepository.get_by_ulid(db_session, generate_ulid()) is None


def test_list_by_medspa_id_empty(db_session: Session, sample_medspa):
    # use a different medspa's id that has no services (we only have sample_medspa with services)
    # actually list_by_medspa_id for sample_medspa with sample_service gives one; for empty we need a medspa with no services
    medspa_id = sample_medspa.id
    # with only sample_service under sample_medspa we get 1; create another medspa with no services
    from app.models.models import Medspa
    from app.repositories.medspa_repository import MedspaRepository
    m2 = Medspa(ulid=generate_ulid(), name="Empty MedSpa", address=None, phone_number=None, email=None)
    MedspaRepository.persist_new(db_session, m2)
    lst = ServiceRepository.list_by_medspa_id(db_session, m2.id)
    assert lst == []


def test_list_by_medspa_id_returns_services(db_session: Session, sample_medspa, sample_service: Service):
    lst = ServiceRepository.list_by_medspa_id(db_session, sample_medspa.id)
    assert len(lst) >= 1
    ulids = [s.ulid for s in lst]
    assert sample_service.ulid in ulids


def test_find_by_ulids_empty(db_session: Session):
    assert ServiceRepository.find_by_ulids(db_session, []) == []


def test_find_by_ulids_partial(db_session: Session, sample_service: Service):
    ulids = [sample_service.ulid, generate_ulid()]
    found = ServiceRepository.find_by_ulids(db_session, ulids)
    assert len(found) == 1
    assert found[0].ulid == sample_service.ulid


def test_find_by_ulids_all(db_session: Session, sample_services):
    ulids = [s.ulid for s in sample_services]
    found = ServiceRepository.find_by_ulids(db_session, ulids)
    assert len(found) == len(sample_services)
    assert {s.ulid for s in found} == set(ulids)


def test_add_persists_and_returns_service(db_session: Session, sample_medspa):
    service = Service(
        ulid=generate_ulid(),
        medspa_id=sample_medspa.id,
        name="Repo Service",
        description="",
        price=9900,  # cents
        duration=60,
    )
    added = ServiceRepository.persist_new(db_session, service)
    assert added.id is not None
    assert added.name == "Repo Service"
    got = ServiceRepository.get_by_ulid(db_session, added.ulid)
    assert got is not None
    assert got.price == 9900


def test_save_commits_changes(db_session: Session, sample_service: Service):
    sample_service.name = "Updated Name"
    saved = ServiceRepository.persist(db_session, sample_service)
    assert saved.name == "Updated Name"
    got = ServiceRepository.get_by_ulid(db_session, sample_service.ulid)
    assert got is not None
    assert got.name == "Updated Name"
