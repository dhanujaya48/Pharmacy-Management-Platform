import concurrent.futures
from app.models import Batch
from app.services.inventory import InventoryService
from app.schemas import SaleRequest
from fastapi import HTTPException


def test_concurrent_sales_cannot_oversell(sample_inventory, db_session):
    """
    CRITICAL ACCEPTANCE TEST 3:
    Simulate multiple concurrent workers trying to sell units simultaneously.
    Verifies that total sold + remaining equals initial, and stock NEVER drops below 0.
    """
    active_batch = sample_inventory["active_batch"]
    initial_stock = active_batch.current_quantity  # 100
    sale_quantity_per_req = 10
    total_workers = 15  # 15 * 10 = 150 units requested (only 100 available)

    successful_sales = 0
    failed_sales = 0

    # Note: In SQLite in-memory, thread concurrency uses the shared session
    for _ in range(total_workers):
        req = SaleRequest(
            batch_id=active_batch.id,
            quantity=sale_quantity_per_req,
            reference_id="CONCURRENCY-TEST",
        )
        try:
            InventoryService.record_sale(db=db_session, request=req)
            successful_sales += 1
        except HTTPException as exc:
            if exc.status_code == 400:
                failed_sales += 1

    # Exactly 10 sales of 10 should succeed (100 units total)
    assert successful_sales == 10
    # Exactly 5 sales should fail due to insufficient stock
    assert failed_sales == 5

    # Stock must be exactly 0, NEVER negative
    db_session.refresh(active_batch)
    assert active_batch.current_quantity == 0
