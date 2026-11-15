from datetime import date
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models import Medicine, Batch, StockMovement, MovementType
from app.logging_config import logger


def seed_database(db: Session | None = None):
    close_after = False
    if db is None:
        db = SessionLocal()
        close_after = True

    try:
        # Check if already seeded
        if db.query(Medicine).first():
            logger.info("Database already seeded with synthetic records. Skipping.")
            return

        logger.info("Seeding synthetic pharmacy records...")

        # 1. Paracetamol
        para = Medicine(
            name="Paracetamol 500mg",
            sku="MED-PARA-500",
            dosage_form="Tablet",
            unit_price=2.50,
            description="Antipyretic and mild pain reliever",
        )
        db.add(para)
        db.flush()

        # Valid Batch
        b001 = Batch(
            medicine_id=para.id,
            batch_number="B001",
            manufacturing_date=date(2024, 1, 1),
            expiry_date=date(2027, 12, 31),
            initial_quantity=100,
            current_quantity=100,
        )
        # Expired Batch for Acceptance Test verification!
        b002_exp = Batch(
            medicine_id=para.id,
            batch_number="B002-EXPIRED",
            manufacturing_date=date(2022, 1, 1),
            expiry_date=date(2023, 12, 31),
            initial_quantity=25,
            current_quantity=25,
        )
        db.add_all([b001, b002_exp])
        db.flush()

        # Movements
        m1 = StockMovement(
            batch_id=b001.id,
            movement_type=MovementType.PURCHASE,
            quantity=100,
            previous_quantity=0,
            new_quantity=100,
            reason="Synthetic seed initial stock",
            reference_id="SEED-001",
        )
        m2 = StockMovement(
            batch_id=b002_exp.id,
            movement_type=MovementType.PURCHASE,
            quantity=25,
            previous_quantity=0,
            new_quantity=25,
            reason="Synthetic seed expired stock for test verification",
            reference_id="SEED-002",
        )
        db.add_all([m1, m2])

        # 2. Amoxicillin
        amox = Medicine(
            name="Amoxicillin 250mg",
            sku="MED-AMOX-250",
            dosage_form="Capsule",
            unit_price=6.00,
            description="Broad-spectrum antibiotic",
        )
        db.add(amox)
        db.flush()

        b_amox = Batch(
            medicine_id=amox.id,
            batch_number="B003",
            manufacturing_date=date(2024, 2, 1),
            expiry_date=date(2028, 1, 31),
            initial_quantity=50,
            current_quantity=50,
        )
        db.add(b_amox)
        db.flush()

        m3 = StockMovement(
            batch_id=b_amox.id,
            movement_type=MovementType.PURCHASE,
            quantity=50,
            previous_quantity=0,
            new_quantity=50,
            reason="Synthetic seed initial stock",
            reference_id="SEED-003",
        )
        db.add(m3)

        # 3. Cetirizine
        cet = Medicine(
            name="Cetirizine 10mg",
            sku="MED-CET-010",
            dosage_form="Tablet",
            unit_price=3.25,
            description="Second-generation antihistamine for allergies",
        )
        db.add(cet)
        db.flush()

        b_cet = Batch(
            medicine_id=cet.id,
            batch_number="B004",
            manufacturing_date=date(2024, 3, 1),
            expiry_date=date(2027, 3, 31),
            initial_quantity=75,
            current_quantity=75,
        )
        db.add(b_cet)
        db.flush()

        m4 = StockMovement(
            batch_id=b_cet.id,
            movement_type=MovementType.PURCHASE,
            quantity=75,
            previous_quantity=0,
            new_quantity=75,
            reason="Synthetic seed initial stock",
            reference_id="SEED-004",
        )
        db.add(m4)

        db.commit()
        logger.info("Successfully seeded database with synthetic medicines, batches, and movements.")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed database: {e}")
        raise
    finally:
        if close_after:
            db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_database()
