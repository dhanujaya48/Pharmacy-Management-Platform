from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Batch, Medicine, StockMovement, MovementType
from app.schemas import BatchCreate, BatchResponse
from app.logging_config import logger

router = APIRouter(prefix="/batches", tags=["Batches"])


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(batch_in: BatchCreate, db: Session = Depends(get_db)):
    # 1. Verify medicine exists
    medicine = db.query(Medicine).filter(Medicine.id == batch_in.medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {batch_in.medicine_id} does not exist",
        )

    # 2. Check batch uniqueness per medicine
    existing = (
        db.query(Batch)
        .filter(
            Batch.medicine_id == batch_in.medicine_id,
            Batch.batch_number == batch_in.batch_number,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Batch '{batch_in.batch_number}' already exists for "
                f"medicine '{medicine.name}'"
            ),
        )

    batch = Batch(
        medicine_id=batch_in.medicine_id,
        batch_number=batch_in.batch_number,
        manufacturing_date=batch_in.manufacturing_date,
        expiry_date=batch_in.expiry_date,
        initial_quantity=batch_in.initial_quantity,
        current_quantity=batch_in.initial_quantity,
        is_active=True,
    )
    db.add(batch)
    db.flush()

    # Create initial audit movement
    initial_movement = StockMovement(
        batch_id=batch.id,
        movement_type=MovementType.PURCHASE,
        quantity=batch.initial_quantity,
        previous_quantity=0,
        new_quantity=batch.initial_quantity,
        reason="Initial batch registration",
        reference_id=f"INIT-{batch.batch_number}",
    )
    db.add(initial_movement)
    db.commit()
    db.refresh(batch)

    logger.info(
        f"Created batch {batch.batch_number} for medicine {medicine.name} "
        f"with initial stock {batch.initial_quantity}"
    )
    return batch


@router.get("", response_model=List[BatchResponse])
def list_batches(
    medicine_id: Optional[int] = Query(None, description="Filter by medicine ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Batch)
    if medicine_id:
        query = query.filter(Batch.medicine_id == medicine_id)
    return query.order_by(Batch.expiry_date.asc()).offset(skip).limit(limit).all()


@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with ID {batch_id} not found",
        )
    return batch
