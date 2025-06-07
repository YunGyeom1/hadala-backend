import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.user.models import User
from app.farmer.models import Farmer
from app.core.auth.utils import create_access_token


@pytest.fixture
def farmer_payload():
    return {
        "name": "김철수",
        "address": "경기도 고양시",
        "farm_size_m2": 2500.0,
        "annual_output_kg": 3200.0,
        "farm_members": 3
    }


@pytest.fixture
def auth_headers(test_user: User):
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


def test_create_farmer(client: TestClient, test_user: User, auth_headers: dict, db: Session, farmer_payload: dict):
    response = client.post("/farmers/", json=farmer_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == farmer_payload["name"]
    assert data["address"] == farmer_payload["address"]
    assert data["user_id"] == str(test_user.id)
    assert "id" in data
    assert "created_at" in data


def test_get_farmer(client: TestClient, test_farmer: Farmer, auth_headers: dict):
    response = client.get(f"/farmers/{test_farmer.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_farmer.id)
    assert data["name"] == test_farmer.name


def test_update_farmer(client: TestClient, test_farmer: Farmer, auth_headers: dict):
    update_payload = {
        "name": "변경된 이름",
        "address": "강원도 홍천군"
    }
    response = client.put(
        f"/farmers/{test_farmer.id}",
        json=update_payload,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["address"] == update_payload["address"]


def test_unauthorized_update_farmer(client: TestClient, test_farmer: Farmer, db: Session):
    attacker = User(
        email="hacker@example.com",
        name="hacker",
        oauth_provider="google",
        oauth_sub="hacksocial"
    )
    db.add(attacker)
    db.commit()
    db.refresh(attacker)

    fake_token = create_access_token({"sub": str(attacker.id)})
    headers = {"Authorization": f"Bearer {fake_token}"}

    response = client.put(
        f"/farmers/{test_farmer.id}",
        json={"name": "해커의 시도"},
        headers=headers
    )
    assert response.status_code == 403


def test_filter_farmers(client: TestClient, test_farmer: Farmer):
    response = client.get("/farmers/?address=경기도")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any("경기도" in farmer["address"] for farmer in data if "address" in farmer)