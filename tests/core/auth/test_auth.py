import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.core.auth.utils import create_access_token, create_refresh_token
from app.user.models import User


@pytest.fixture
def fake_user_id():
    return uuid4()

def test_verify_valid_access_token(client: TestClient, fake_user_id):
    token = create_access_token({"sub": str(fake_user_id)})
    response = client.post("/auth/verify", json={"access_token": token})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["user_id"] == str(fake_user_id)

def test_verify_invalid_access_token(client: TestClient):
    response = client.post("/auth/verify", json={"access_token": "invalid.token"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "error" in data

def test_refresh_token_success(client: TestClient, fake_user_id):
    refresh_token = create_refresh_token({"sub": str(fake_user_id)})
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_refresh_token_invalid(client: TestClient):
    response = client.post("/auth/refresh", json={"refresh_token": "invalid.token"})
    assert response.status_code == 401