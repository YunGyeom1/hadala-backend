import pytest
from fastapi.testclient import TestClient
from app.core.auth.utils import create_refresh_token
from tests.factories import create_user, create_token_pair


def test_verify_valid_access_token(client: TestClient, db):
    user = create_user(db)
    access_token, _ = create_token_pair(user)
    response = client.post("/auth/verify", json={"access_token": access_token})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["user_id"] == str(user.id)


def test_verify_invalid_access_token(client: TestClient):
    response = client.post("/auth/verify", json={"access_token": "invalid.token"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "error" in data


def test_refresh_token_success(client: TestClient, db):
    user = create_user(db)
    _, refresh_token = create_token_pair(user)
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid(client: TestClient):
    response = client.post("/auth/refresh", json={"refresh_token": "invalid.token"})
    assert response.status_code == 401