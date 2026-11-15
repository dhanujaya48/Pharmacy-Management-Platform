from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Medicine
from app.schemas import MedicineCreate, MedicineUpdate, MedicineResponse
from app.logging_config import logger

router = APIRouter(prefix="/medicines", tags=["Medicines"])


@router.post("", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
def create_medicine(medicine_in: MedicineCreate, db: Session = Depends(get_db)):
    # Check duplicate SKU
    existing = db.query(Medicine).filter(Medicine.sku == medicine_in.sku).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Medicine with SKU '{medicine_in.sku}' already exists",
        )

    medicine = Medicine(
        name=medicine_in.name,
        sku=medicine_in.sku,
        dosage_form=medicine_in.dosage_form,
        unit_price=medicine_in.unit_price,
        description=medicine_in.description,
    )
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    logger.info(f"Created medicine: {medicine.name} (SKU: {medicine.sku})")
    return medicine


@router.get("", response_model=List[MedicineResponse])
def list_medicines(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    db: Session = Depends(get_db),
):
    query = db.query(Medicine)
    if search:
        query = query.filter(
            (Medicine.name.ilike(f"%{search}%")) | (Medicine.sku.ilike(f"%{search}%"))
        )
    return query.offset(skip).limit(limit).all()


@router.get("/{medicine_id}", response_model=MedicineResponse)
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {medicine_id} not found",
        )
    return medicine


@router.put("/{medicine_id}", response_model=MedicineResponse)
def update_medicine(
    medicine_id: int, medicine_in: MedicineUpdate, db: Session = Depends(get_db)
):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {medicine_id} not found",
        )

    update_data = medicine_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(medicine, field, value)

    db.commit()
    db.refresh(medicine)
    logger.info(f"Updated medicine ID {medicine_id}")
    return medicine


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medicine with ID {medicine_id} not found",
        )
    db.delete(medicine)
    db.commit()
    logger.info(f"Deleted medicine ID {medicine_id}")
    return None
