from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Medicine, Batch
from app.schemas import InventoryReport, MedicineInventorySummary, BatchStockDetail

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/inventory", response_model=InventoryReport)
def get_inventory_report(db: Session = Depends(get_db)):
    today = date.today()
    medicines = db.query(Medicine).all()

    total_batches = 0
    total_units_in_stock = 0
    total_expired_units = 0

    summaries = []

    for med in medicines:
        med_stock = 0
        batch_details = []

        for b in med.batches:
            total_batches += 1
            is_expired = b.expiry_date <= today
            med_stock += b.current_quantity
            total_units_in_stock += b.current_quantity

            if is_expired:
                total_expired_units += b.current_quantity
                status_str = "EXPIRED"
            elif b.current_quantity == 0:
                status_str = "OUT_OF_STOCK"
            else:
                status_str = "ACTIVE"

            batch_details.append(
                BatchStockDetail(
                    batch_id=b.id,
                    batch_number=b.batch_number,
                    expiry_date=b.expiry_date,
                    current_quantity=b.current_quantity,
                    is_expired=is_expired,
                    status=status_str,
                )
            )

        summaries.append(
            MedicineInventorySummary(
                medicine_id=med.id,
                medicine_name=med.name,
                sku=med.sku,
                unit_price=med.unit_price,
                total_stock=med_stock,
                batches=batch_details,
            )
        )

    return InventoryReport(
        generated_at=datetime.now(timezone.utc),
        total_medicines=len(medicines),
        total_batches=total_batches,
        total_units_in_stock=total_units_in_stock,
        total_expired_units=total_expired_units,
        medicines=summaries,
    )
