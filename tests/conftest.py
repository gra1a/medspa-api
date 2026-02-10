import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Use DATABASE_URL if set (e.g. in Docker: postgres_test). Otherwise use localhost:5433
# so local pytest works when test DB is running: docker-compose -f docker-compose.test.yml up -d
from app.db.database import Base, get_db
from app.main import app
from app.models.models import Medspa, Service, Appointment, appointment_services_table
from app.utils.ulid import generate_ulid

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/medspa_test",
)

test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    # Optional: drop tables after all tests (comment out to keep for debugging)
    # Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(setup_test_db):
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        # Truncate so next test has clean DB
        for table in ("appointment_services", "appointments", "services", "medspas"):
            try:
                session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                session.commit()
            except Exception:
                session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_medspa(db_session):
    m = Medspa(
        ulid=generate_ulid(),
        name="Test MedSpa",
        address="123 Test St",
        phone_number="555-0000",
        email="test@test.com",
    )
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


@pytest.fixture
def sample_service(db_session, sample_medspa):
    s = Service(
        ulid=generate_ulid(),
        medspa_id=sample_medspa.id,
        name="Test Service",
        description="A test",
        price=5000,  # cents
        duration=30,
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


@pytest.fixture
def sample_services(db_session, sample_medspa):
    services = [
        Service(
            ulid=generate_ulid(),
            medspa_id=sample_medspa.id,
            name="S1",
            description="",
            price=1000,  # cents
            duration=15,
        ),
        Service(
            ulid=generate_ulid(),
            medspa_id=sample_medspa.id,
            name="S2",
            description="",
            price=2000,  # cents
            duration=30,
        ),
    ]
    for s in services:
        db_session.add(s)
    db_session.commit()
    for s in services:
        db_session.refresh(s)
    return services


@pytest.fixture
def sample_appointment(db_session, sample_medspa, sample_services):
    from datetime import datetime, timezone
    appt = Appointment(
        ulid=generate_ulid(),
        medspa_id=sample_medspa.id,
        start_time=datetime.now(timezone.utc).replace(microsecond=0),
        status="scheduled",
        total_price=3000,  # cents
        total_duration=45,
    )
    db_session.add(appt)
    db_session.flush()
    for s in sample_services:
        db_session.execute(
            appointment_services_table.insert().values(
                appointment_id=appt.id, service_id=s.id
            )
        )
    db_session.commit()
    db_session.refresh(appt)
    return appt
