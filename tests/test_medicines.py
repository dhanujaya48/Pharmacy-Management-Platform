def test_create_and_get_medicine(client):
    payload = {
        "name": "Amoxicillin 500mg",
        "sku": "MED-AMX-500",
        "dosage_form": "Capsule",
        "unit_price": 8.50,
        "description": "Antibiotic",
    }
    create_res = client.post("/medicines", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["id"] is not None
    assert created_data["sku"] == "MED-AMX-500"

    # Query single medicine
    get_res = client.get(f"/medicines/{created_data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Amoxicillin 500mg"


def test_duplicate_sku_rejected(client):
    payload = {
        "name": "Aspirin 100mg",
        "sku": "MED-ASP-100",
        "dosage_form": "Tablet",
        "unit_price": 3.00,
    }
    res1 = client.post("/medicines", json=payload)
    assert res1.status_code == 201

    # Second attempt with same SKU
    res2 = client.post("/medicines", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_list_medicines_with_search(client):
    client.post(
        "/medicines",
        json={"name": "Cetirizine 10mg", "sku": "MED-CET-001", "dosage_form": "Tablet", "unit_price": 2.0},
    )
    client.post(
        "/medicines",
        json={"name": "Ibuprofen 400mg", "sku": "MED-IBU-001", "dosage_form": "Tablet", "unit_price": 4.5},
    )

    search_res = client.get("/medicines?search=Cetirizine")
    assert search_res.status_code == 200
    items = search_res.json()
    assert len(items) == 1
    assert items[0]["sku"] == "MED-CET-001"
