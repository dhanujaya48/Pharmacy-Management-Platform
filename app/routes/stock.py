from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import StockMovement, MovementType
from app.schemas import (
    PurchaseRequest,
    SaleRequest,
    ReturnRequest,
    AdjustmentRequest,
    StockMovementResponse,
)
from app.services.inventory import InventoryService

router = APIRouter(prefix="/stock", tags=["Stock Movements"])


@router.post("/purchase", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
def purchase_stock(request: PurchaseRequest, db: Session = Depends(get_db)):
    return InventoryService.record_purchase(db=db, request=request)


@router.post("/sale", response_model=StockMovementResponse, status_code=status.HTTP_200_OK)
def sell_stock(request: SaleRequest, db: Session = Depends(get_db)):
    """
    Sell medicine from a batch.
    Acceptance Criteria:
    - Fails if batch is expired.
    - Fails if requested quantity exceeds current stock.
    - Concurrency-safe against race conditions.
    """
    return InventoryService.record_sale(db=db, request=request)


@router.post("/return", response_model=StockMovementResponse, status_code=status.HTTP_200_OK)
def return_stock(request: ReturnRequest, db: Session = Depends(get_db)):
    return InventoryService.record_return(db=db, request=request)


@router.post("/adjustment", response_model=StockMovementResponse, status_code=status.HTTP_200_OK)
def adjust_stock(request: AdjustmentRequest, db: Session = Depends(get_db)):
    return InventoryService.record_adjustment(db=db, request=request)


@router.get("/movements", response_model=List[StockMovementResponse])
def get_stock_movements(
    batch_id: Optional[int] = Query(None, description="Filter by batch ID"),
    movement_type: Optional[MovementType] = Query(None, description="Filter by movement type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(StockMovement)
    if batch_id:
        query = query.filter(StockMovement.batch_id == batch_id)
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)

    return query.order_by(StockMovement.created_at.desc()).offset(skip).limit(limit).all()
