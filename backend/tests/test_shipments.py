"""Tests for shipment CRUD endpoints."""
import pytest


async def _auth_headers(client):
    resp = await client.post("/api/auth/register", json={
        "email": "ship_test@example.com",
        "username": "shiptest",
        "password": "Test@1234",
    })
    if resp.status_code == 409:
        resp = await client.post("/api/auth/login", json={
            "email": "ship_test@example.com",
            "password": "Test@1234",
        })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_create_shipment(client):
    headers = await _auth_headers(client)
    resp = await client.post("/api/shipments", headers=headers, json={
        "tracking_number": "TEST001",
        "title": "Test Shipment",
        "origin_location": "New York, USA",
        "destination_location": "London, UK",
        "mode": "air",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["tracking_number"] == "TEST001"
    assert data["risk_score"] is not None
    assert isinstance(data["risk_factors"], str)


@pytest.mark.asyncio
async def test_list_shipments(client):
    headers = await _auth_headers(client)
    # Create one first
    await client.post("/api/shipments", headers=headers, json={
        "tracking_number": "LIST001",
        "title": "List Test",
        "origin_location": "Paris",
        "destination_location": "Tokyo",
    })
    resp = await client.get("/api/shipments", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_shipment(client):
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/shipments", headers=headers, json={
        "tracking_number": "GET001",
        "title": "Get Test",
        "origin_location": "Berlin",
        "destination_location": "Sydney",
    })
    ship_id = create_resp.json()["id"]
    resp = await client.get(f"/api/shipments/{ship_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == ship_id


@pytest.mark.asyncio
async def test_update_shipment(client):
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/shipments", headers=headers, json={
        "tracking_number": "UPD001",
        "title": "Update Test",
        "origin_location": "Madrid",
        "destination_location": "Mumbai",
    })
    ship_id = create_resp.json()["id"]
    resp = await client.patch(f"/api/shipments/{ship_id}", headers=headers, json={
        "status": "in_transit",
        "carrier": "Test Carrier",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_transit"


@pytest.mark.asyncio
async def test_delete_shipment(client):
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/shipments", headers=headers, json={
        "tracking_number": "DEL001",
        "title": "Delete Test",
        "origin_location": "Rome",
        "destination_location": "Cairo",
    })
    ship_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/shipments/{ship_id}", headers=headers)
    assert resp.status_code == 204
    # Verify gone
    resp = await client.get(f"/api/shipments/{ship_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_add_tracking_event(client):
    headers = await _auth_headers(client)
    create_resp = await client.post("/api/shipments", headers=headers, json={
        "tracking_number": "EVT001",
        "title": "Event Test",
        "origin_location": "Seoul",
        "destination_location": "Amsterdam",
    })
    ship_id = create_resp.json()["id"]
    resp = await client.post(f"/api/shipments/{ship_id}/events", headers=headers, json={
        "status": "in_transit",
        "location": "Beijing, China",
        "description": "Transit stop",
    })
    assert resp.status_code == 201
    assert resp.json()["status"] == "in_transit"


@pytest.mark.asyncio
async def test_search_shipments(client):
    headers = await _auth_headers(client)
    await client.post("/api/shipments", headers=headers, json={
        "tracking_number": "SEARCH001",
        "title": "Unique XYZ Cargo",
        "origin_location": "Vienna",
        "destination_location": "Nairobi",
    })
    resp = await client.get("/api/shipments?search=XYZ", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("XYZ" in i["title"] for i in items)


@pytest.mark.asyncio
async def test_duplicate_tracking_number(client):
    headers = await _auth_headers(client)
    payload = {
        "tracking_number": "DUP001",
        "title": "Dup Test",
        "origin_location": "Oslo",
        "destination_location": "Bangkok",
    }
    await client.post("/api/shipments", headers=headers, json=payload)
    resp = await client.post("/api/shipments", headers=headers, json=payload)
    assert resp.status_code == 409
