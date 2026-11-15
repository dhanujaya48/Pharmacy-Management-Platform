from app.models import Batch, StockMovement, MovementType


def test_sale_against_expired_batch_fails_without_changing_stock(client, sample_inventory, db_session):
    """
    CRITICAL ACCEPTANCE TEST 1:
    A sale against an expired batch MUST FAIL with HTTP 400
    and stock MUST remain completely unchanged.
    """
    expired_batch = sample_inventory["expired_batch"]
    initial_stock = expired_batch.current_quantity

    # Attempt to sell 5 units from expired batch
    sale_payload = {
        "batch_id": expired_batch.id,
        "quantity": 5,
        "reference_id": "TEST-SALE-EXPIRED",
        "reason": "Prescription sale attempt",
    }
    response = client.post("/stock/sale", json=sale_payload)

    # 1. Verify HTTP 400 rejection
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

    # 2. Verify batch stock was NOT changed
    db_session.refresh(expired_batch)
    assert expired_batch.current_quantity == initial_stock

    # 3. Verify no SALE movement record was created
    sale_movements = (
        db_session.query(StockMovement)
        .filter(
            StockMovement.batch_id == expired_batch.id,
            StockMovement.movement_type == MovementType.SALE,
        )
        .all()
    )
    assert len(sale_movements) == 0


def test_sale_exceeding_available_stock_fails_without_changing_stock(client, sample_inventory, db_session):
    """
    CRITICAL ACCEPTANCE TEST 2:
    A sale exceeding batch quantity MUST FAIL with HTTP 400
    and stock MUST remain completely unchanged.
    """
    active_batch = sample_inventory["active_batch"]
    initial_stock = active_batch.current_quantity  # 100

    # Attempt to sell 150 units when only 100 available
    sale_payload = {
        "batch_id": active_batch.id,
        "quantity": 150,
        "reference_id": "TEST-SALE-OVERSELL",
        "reason": "Bulk order attempt",
    }
    response = client.post("/stock/sale", json=sale_payload)

    # 1. Verify HTTP 400 rejection
    assert response.status_code == 400
    assert "insufficient stock" in response.json()["detail"].lower()

    # 2. Verify batch stock was NOT changed
    db_session.refresh(active_batch)
    assert active_batch.current_quantity == initial_stock


def test_successful_sale_deducts_stock_and_creates_audit_record(client, sample_inventory, db_session):
    active_batch = sample_inventory["active_batch"]
    initial_stock = active_batch.current_quantity  # 100

    sale_payload = {
        "batch_id": active_batch.id,
        "quantity": 25,
        "reference_id": "INV-2026-999",
        "reason": "Direct OTC sale",
    }
    response = client.post("/stock/sale", json=sale_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["quantity"] == 25
    assert data["previous_quantity"] == 100
    assert data["new_quantity"] == 75
    assert data["movement_type"] == "SALE"

    # Verify database state
    db_session.refresh(active_batch)
    assert active_batch.current_quantity == 75


def test_negative_quantity_sale_rejected(client, sample_inventory):
    active_batch = sample_inventory["active_batch"]
    sale_payload = {
        "batch_id": active_batch.id,
        "quantity": -10,  # Negative!
        "reference_id": "INV-ILLEGAL",
    }
    response = client.post("/stock/sale", json=sale_payload)
    assert response.status_code == 422


def test_stock_purchase_increments_stock(client, sample_inventory, db_session):
    active_batch = sample_inventory["active_batch"]
    initial_stock = active_batch.current_quantity  # 100

    purchase_payload = {
        "batch_id": active_batch.id,
        "quantity": 50,
        "reference_id": "PO-2026-001",
        "reason": "Supplier shipment receipt",
    }
    response = client.post("/stock/purchase", json=purchase_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["previous_quantity"] == 100
    assert data["new_quantity"] == 150

    db_session.refresh(active_batch)
    assert active_batch.current_quantity == 150


def test_stock_return_increments_stock(client, sample_inventory, db_session):
    active_batch = sample_inventory["active_batch"]
    initial_stock = active_batch.current_quantity

    return_payload = {
        "batch_id": active_batch.id,
        "quantity": 5,
        "reference_id": "RET-2026-001",
        "reason": "Customer returned unopened pack",
    }
    response = client.post("/stock/return", json=return_payload)
    assert response.status_code == 200

    db_session.refresh(active_batch)
    assert active_batch.current_quantity == initial_stock + 5


def test_stock_adjustment_updates_stock_and_records_audit(client, sample_inventory, db_session):
    active_batch = sample_inventory["active_batch"]

    adj_payload = {
        "batch_id": active_batch.id,
        "adjusted_quantity": 90,
        "reference_id": "AUDIT-001",
        "reason": "Damaged goods discarded",
    }
    response = client.post("/stock/adjustment", json=adj_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["previous_quantity"] == 100
    assert data["new_quantity"] == 90
    assert data["quantity"] == 10
    assert "Delta: -10" in data["reason"]

    db_session.refresh(active_batch)
    assert active_batch.current_quantity == 90


def test_audit_movements_query(client, sample_inventory):
    # Perform a purchase and a sale
    active_batch = sample_inventory["active_batch"]
    client.post("/stock/purchase", json={"batch_id": active_batch.id, "quantity": 10})
    client.post("/stock/sale", json={"batch_id": active_batch.id, "quantity": 5})

    res = client.get(f"/stock/movements?batch_id={active_batch.id}")
    assert res.status_code == 200
    movements = res.json()
    assert len(movements) >= 2
    types = [m["movement_type"] for m in movements]
    assert "SALE" in types
    assert "PURCHASE" in types
