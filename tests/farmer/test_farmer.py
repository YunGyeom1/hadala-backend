import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.factories import (
    create_user,
    create_token_pair,
    create_farmer
)

@pytest.fixture
def farmer_payload():
    return {
        "name": "테스트농부",
        "address": "경기도 남양주시",
        "farm_size_m2": 1200.0,
        "annual_output_kg": 2000.0,
        "farm_members": 4
    }

def test_create_farmer(client: TestClient, db: Session, farmer_payload):
    user = create_user(db)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = farmer_payload

    response = client.post("/farmers/", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["address"] == payload["address"]
    assert data["user_id"] == str(user.id)
    assert "id" in data
    assert "created_at" in data


def test_get_farmer(client: TestClient, db: Session):
    user = create_user(db)
    farmer = create_farmer(db, user.id)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get(f"/farmers/{farmer.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(farmer.id)
    assert data["name"] == farmer.name


def test_update_farmer(client: TestClient, db: Session):
    user = create_user(db)
    farmer = create_farmer(db, user.id)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    update_payload = {
        "name": "변경된 이름",
        "address": "강원도 홍천군"
    }

    response = client.put(
        f"/farmers/{farmer.id}",
        json=update_payload,
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["address"] == update_payload["address"]


def test_unauthorized_update_farmer(client: TestClient, db: Session):
    owner = create_user(db)
    farmer = create_farmer(db, owner.id)

    attacker = create_user(db, email_prefix="hacker", name="해커")
    access_token, _ = create_token_pair(attacker)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.put(
        f"/farmers/{farmer.id}",
        json={"name": "해커의 시도"},
        headers=headers
    )
    assert response.status_code == 403


def test_filter_farmers(client: TestClient, db: Session):
    user = create_user(db)
    farmer = create_farmer(db, user.id, address="경기도 남양주시")

    response = client.get("/farmers/?address=경기도")
    assert response.status_code == 200
