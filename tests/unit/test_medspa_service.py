import pytest
from sqlalchemy.orm import Session

pytestmark = pytest.mark.unit

from app.exceptions import NotFoundError
from app.models.models import Medspa
from app.schemas.medspas import MedspaCreate
from app.services.medspa_service import MedspaService
from app.utils.ulid import generate_ulid


def test_get_medspa_found(db_session: Session, sample_medspa: Medspa):
    got = MedspaService.get_medspa(db_session, sample_medspa.ulid)
    assert got.id == sample_medspa.id
    assert got.ulid == sample_medspa.ulid
    assert got.name == sample_medspa.name


def test_get_medspa_not_found(db_session: Session):
    with pytest.raises(NotFoundError, match="Medspa not found"):
        MedspaService.get_medspa(db_session, generate_ulid())


def test_list_medspas_empty(db_session: Session):
    # db_session is fresh per test; without sample_medspa we may have 0 from truncate
    lst = MedspaService.list_medspas(db_session)
    assert isinstance(lst, list)


def test_list_medspas_returns_all(db_session: Session, sample_medspa: Medspa):
    lst = MedspaService.list_medspas(db_session)
    assert len(lst) >= 1
    ulids = [m.ulid for m in lst]
    assert sample_medspa.ulid in ulids


def test_create_medspa_success(db_session: Session):
    data = MedspaCreate(
        name="New MedSpa",
        address="100 Main St",
        phone_number="555-1234",
        email="contact@example.com",
    )
    medspa = MedspaService.create_medspa(db_session, data)
    assert medspa.id is not None
    assert medspa.ulid is not None
    assert medspa.name == "New MedSpa"
    assert medspa.address == "100 Main St"
    got = MedspaService.get_medspa(db_session, medspa.ulid)
    assert got.name == medspa.name
