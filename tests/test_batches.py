def test_create_batch_success(client, sample_inventory):
    med_id = sample_inventory["medicine"].id
    payload = {
        "medicine_id": med_id,
        "batch_number": "B999-NEW",
        "manufacturing_date": "2025-01-01",
        "expiry_date": "2028-01-01",
        "initial_quantity": 200,
    }
    res = client.post("/batches", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["batch_number"] == "B999-NEW"
    assert data["current_quantity"] == 200


def test_batch_invalid_expiry_before_mfg(client, sample_inventory):
    med_id = sample_inventory["medicine"].id
    payload = {
        "medicine_id": med_id,
        "batch_number": "B_INVALID_DATES",
        "manufacturing_date": "2026-01-01",
        "expiry_date": "2024-01-01",  # Expiry earlier than mfg!
        "initial_quantity": 50,
    }
    res = client.post("/batches", json=payload)
    assert res.status_code == 422  # Pydantic validation error


def test_batch_negative_quantity_rejected(client, sample_inventory):
    med_id = sample_inventory["medicine"].id
    payload = {
        "medicine_id": med_id,
        "batch_number": "B_NEG_QTY",
        "manufacturing_date": "2025-01-01",
        "expiry_date": "2027-01-01",
        "initial_quantity": -10,  # Negative quantity!
    }
    res = client.post("/batches", json=payload)
    assert res.status_code == 422
