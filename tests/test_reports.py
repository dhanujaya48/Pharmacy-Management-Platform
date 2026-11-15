def test_inventory_report_structure_and_counts(client, sample_inventory):
    res = client.get("/reports/inventory")
    assert res.status_code == 200
    data = res.json()

    assert data["total_medicines"] >= 1
    assert data["total_batches"] >= 2
    assert "total_units_in_stock" in data
    assert "total_expired_units" in data
    assert data["total_expired_units"] == 50  # From sample_inventory expired batch

    # Check medicines list
    medicines = data["medicines"]
    assert len(medicines) >= 1
    para = next(m for m in medicines if m["sku"] == "MED-PARA-500")
    assert len(para["batches"]) == 2

    # Check status labeling
    statuses = [b["status"] for b in para["batches"]]
    assert "EXPIRED" in statuses
    assert "ACTIVE" in statuses
