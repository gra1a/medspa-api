import pytest
from sqlalchemy.orm import Session

from app.models.models import Service
from app.repositories.service_repository import ServiceRepository
from app.utils.ulid import generate_id

pytestmark = pytest.mark.unit


def test_get_by_id_found(db_session: Session, sample_service: Service):
    got = ServiceRepository.get_by_id(db_session, sample_service.id)
    assert got is not None
    assert got.id == sample_service.id
    assert got.name == sample_service.name


def test_get_by_id_not_found(db_session: Session):
    assert ServiceRepository.get_by_id(db_session, generate_id()) is None


def test_list_by_medspa_id_empty(db_session: Session, sample_medspa):
    # create another medspa with no services
    from app.models.models import Medspa
    from app.repositories.medspa_repository import MedspaRepository
    m2 = Medspa(id=generate_id(), name="Empty MedSpa", address=None, phone_number=None, email=None)
    MedspaRepository.persist_new(db_session, m2)
    lst = ServiceRepository.list_by_medspa_id(db_session, m2.id, limit=10)
    assert lst == []


def test_list_by_medspa_id_returns_services(db_session: Session, sample_medspa, sample_service: Service):
    lst = ServiceRepository.list_by_medspa_id(db_session, sample_medspa.id, limit=10)
    assert len(lst) >= 1
    ids = [s.id for s in lst]
    assert sample_service.id in ids


def test_find_by_ids_empty(db_session: Session):
    assert ServiceRepository.find_by_ids(db_session, []) == []


def test_find_by_ids_partial(db_session: Session, sample_service: Service):
    ids = [sample_service.id, generate_id()]
    found = ServiceRepository.find_by_ids(db_session, ids)
    assert len(found) == 1
    assert found[0].id == sample_service.id


def test_find_by_ids_all(db_session: Session, sample_services):
    ids = [s.id for s in sample_services]
    found = ServiceRepository.find_by_ids(db_session, ids)
    assert len(found) == len(sample_services)
    assert {s.id for s in found} == set(ids)


def test_add_persists_and_returns_service(db_session: Session, sample_medspa):
    service = Service(
        id=generate_id(),
        medspa_id=sample_medspa.id,
        name="Repo Service",
        description="",
        price=9900,  # cents
        duration=60,
    )
    added = ServiceRepository.upsert_by_id(db_session, service)
    assert added.id is not None
    assert added.name == "Repo Service"
    db_session.commit()
    got = ServiceRepository.get_by_id(db_session, added.id)
    assert got is not None
    assert got.price == 9900


def test_save_commits_changes(db_session: Session, sample_service: Service):
    sample_service.name = "Updated Name"
    saved = ServiceRepository.upsert_by_id(db_session, sample_service)
    assert saved.name == "Updated Name"
    got = ServiceRepository.get_by_id(db_session, sample_service.id)
    assert got is not None
    assert got.name == "Updated Name"
