import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Medicine, Batch, StockMovement, MovementType

# In-memory SQLite for high-speed, isolated deterministic testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh tables for every individual test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_inventory(db_session):
    """Create a sample medicine with one active batch and one expired batch."""
    med = Medicine(
        name="Paracetamol 500mg",
        sku="MED-PARA-500",
        dosage_form="Tablet",
        unit_price=2.50,
        description="Analgesic",
    )
    db_session.add(med)
    db_session.flush()

    # Active batch: 100 units, expires in 2028
    active_batch = Batch(
        medicine_id=med.id,
        batch_number="B001",
        manufacturing_date=date(2024, 1, 1),
        expiry_date=date(2028, 12, 31),
        initial_quantity=100,
        current_quantity=100,
        is_active=True,
    )

    # Expired batch: 50 units, expired in 2023
    expired_batch = Batch(
        medicine_id=med.id,
        batch_number="B002-EXP",
        manufacturing_date=date(2022, 1, 1),
        expiry_date=date(2023, 1, 1),
        initial_quantity=50,
        current_quantity=50,
        is_active=True,
    )

    db_session.add_all([active_batch, expired_batch])
    db_session.flush()

    # Audit records
    m1 = StockMovement(
        batch_id=active_batch.id,
        movement_type=MovementType.PURCHASE,
        quantity=100,
        previous_quantity=0,
        new_quantity=100,
        reason="Initial seed",
    )
    m2 = StockMovement(
        batch_id=expired_batch.id,
        movement_type=MovementType.PURCHASE,
        quantity=50,
        previous_quantity=0,
        new_quantity=50,
        reason="Initial seed",
    )
    db_session.add_all([m1, m2])
    db_session.commit()

    return {
        "medicine": med,
        "active_batch": active_batch,
        "expired_batch": expired_batch,
    }
