from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import Batch, StockMovement, MovementType
from app.schemas import PurchaseRequest, SaleRequest, ReturnRequest, AdjustmentRequest
from app.logging_config import logger


class InventoryService:
    @staticmethod
    def _get_batch_for_update(db: Session, batch_id: int) -> Batch:
        """
        Fetch batch with pessimistic row-level locking (SELECT ... FOR UPDATE)
        to prevent race conditions and concurrent overselling.
        """
        query = db.query(Batch).filter(Batch.id == batch_id)
        if db.bind and db.bind.dialect.name != "sqlite":
            query = query.with_for_update()

        batch = query.first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with ID {batch_id} not found",
            )
        return batch

    @classmethod
    def record_sale(cls, db: Session, request: SaleRequest) -> StockMovement:
        """
        Process a sale transaction.
        Domain Rules:
        1. Batch must exist.
        2. Sale against expired batch must FAIL without changing stock.
        3. Sale exceeding current quantity must FAIL without changing stock.
        4. Must be concurrency-safe.
        """
        batch = cls._get_batch_for_update(db, batch_id=request.batch_id)

        # Rule 1: Expiry validation
        today = date.today()
        if batch.expiry_date <= today:
            logger.warning(
                f"Rejected sale: Batch {batch.batch_number} expired on {batch.expiry_date}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Sale rejected: Batch '{batch.batch_number}' expired on "
                    f"{batch.expiry_date}. Sales from expired batches are prohibited."
                ),
            )

        # Rule 2: Quantity validation
        if batch.current_quantity < request.quantity:
            logger.warning(
                f"Rejected sale: Insufficient stock for batch {batch.batch_number}. "
                f"Requested: {request.quantity}, Available: {batch.current_quantity}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Sale rejected: Insufficient stock for batch '{batch.batch_number}'. "
                    f"Requested {request.quantity}, but only {batch.current_quantity} available."
                ),
            )

        # Apply stock deduction
        prev_qty = batch.current_quantity
        new_qty = prev_qty - request.quantity
        batch.current_quantity = new_qty

        # Record auditable movement
        movement = StockMovement(
            batch_id=batch.id,
            movement_type=MovementType.SALE,
            quantity=request.quantity,
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            reason=request.reason,
            reference_id=request.reference_id,
        )
        db.add(movement)
        db.commit()
        db.refresh(movement)

        logger.info(
            f"Sale recorded: Batch {batch.batch_number}, Quantity {request.quantity}, "
            f"Remaining: {new_qty}, Ref: {request.reference_id}"
        )
        return movement

    @classmethod
    def record_purchase(cls, db: Session, request: PurchaseRequest) -> StockMovement:
        """
        Process a stock purchase/restock transaction.
        """
        batch = cls._get_batch_for_update(db, batch_id=request.batch_id)

        prev_qty = batch.current_quantity
        new_qty = prev_qty + request.quantity
        batch.current_quantity = new_qty

        movement = StockMovement(
            batch_id=batch.id,
            movement_type=MovementType.PURCHASE,
            quantity=request.quantity,
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            reason=request.reason,
            reference_id=request.reference_id,
        )
        db.add(movement)
        db.commit()
        db.refresh(movement)

        logger.info(
            f"Purchase recorded: Batch {batch.batch_number}, Added {request.quantity}, "
            f"New Total: {new_qty}, Ref: {request.reference_id}"
        )
        return movement

    @classmethod
    def record_return(cls, db: Session, request: ReturnRequest) -> StockMovement:
        """
        Process a customer/dispensary return into batch stock.
        """
        batch = cls._get_batch_for_update(db, batch_id=request.batch_id)

        prev_qty = batch.current_quantity
        new_qty = prev_qty + request.quantity
        batch.current_quantity = new_qty

        movement = StockMovement(
            batch_id=batch.id,
            movement_type=MovementType.RETURN,
            quantity=request.quantity,
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            reason=request.reason,
            reference_id=request.reference_id,
        )
        db.add(movement)
        db.commit()
        db.refresh(movement)

        logger.info(
            f"Return recorded: Batch {batch.batch_number}, Returned {request.quantity}, "
            f"New Total: {new_qty}, Ref: {request.reference_id}"
        )
        return movement

    @classmethod
    def record_adjustment(cls, db: Session, request: AdjustmentRequest) -> StockMovement:
        """
        Perform a physical inventory audit adjustment.
        """
        batch = cls._get_batch_for_update(db, batch_id=request.batch_id)

        prev_qty = batch.current_quantity
        target_qty = request.adjusted_quantity

        if target_qty == prev_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Adjusted quantity ({target_qty}) is identical to current stock ({prev_qty})",
            )

        delta = target_qty - prev_qty
        batch.current_quantity = target_qty

        movement = StockMovement(
            batch_id=batch.id,
            movement_type=MovementType.ADJUSTMENT,
            quantity=abs(delta),
            previous_quantity=prev_qty,
            new_quantity=target_qty,
            reason=f"{request.reason} (Delta: {delta:+d})",
            reference_id=request.reference_id,
        )
        db.add(movement)
        db.commit()
        db.refresh(movement)

        logger.info(
            f"Stock adjusted: Batch {batch.batch_number}, From {prev_qty} to {target_qty}, "
            f"Delta: {delta:+d}, Reason: {request.reason}"
        )
        return movement
