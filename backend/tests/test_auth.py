"""Tests for authentication endpoints."""
import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "Test@1234",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "username": "dupuser1", "password": "Test@1234"}
    await client.post("/api/auth/register", json=payload)
    # Duplicate email
    resp = await client.post("/api/auth/register", json={
        **payload, "username": "dupuser2"
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    # Register first
    await client.post("/api/auth/register", json={
        "email": "login_test@example.com",
        "username": "logintest",
        "password": "Test@1234",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "login_test@example.com",
        "password": "Test@1234",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "email": "wp@example.com", "username": "wpuser", "password": "Test@1234"
    })
    resp = await client.post("/api/auth/login", json={
        "email": "wp@example.com", "password": "wrong"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client):
    # Register and get token
    reg_resp = await client.post("/api/auth/register", json={
        "email": "me_test@example.com",
        "username": "metest",
        "password": "Test@1234",
    })
    token = reg_resp.json()["access_token"]
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me_test@example.com"


@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401
