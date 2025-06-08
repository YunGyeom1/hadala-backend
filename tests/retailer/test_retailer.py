import pytest
from fastapi.testclient import TestClient
from tests.factories import create_user, create_token_pair, create_retailer
from app.retailer.models import Retailer
from uuid import uuid4

@pytest.fixture
def retailer_payload():
    return {
        "name": f"테스트마트-{uuid4()}",
        "address": "서울시 강남구",
        "description": "신선식품 전문 마트"
    }

def test_create_retailer(client: TestClient, db, retailer_payload):
    user = create_user(db)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post("/retailers/", json=retailer_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == retailer_payload["name"]
    assert data["address"] == retailer_payload["address"]
    assert data["description"] == retailer_payload["description"]
    assert "id" in data
    assert "created_at" in data
    assert data["user_id"] == str(user.id)


def test_create_retailer_duplicate(client: TestClient, db, retailer_payload):
    user = create_user(db)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    # 첫 번째 생성
    response = client.post("/retailers/", json=retailer_payload, headers=headers)
    assert response.status_code == 200

    # 두 번째 생성 시도
    response = client.post("/retailers/", json=retailer_payload, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "이미 소매상으로 등록된 사용자입니다"


def test_get_retailer(client: TestClient, db):
    user = create_user(db)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}
    retailer = create_retailer(db, user.id)

    response = client.get(f"/retailers/{retailer.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(retailer.id)
    assert data["name"] == retailer.name


def test_update_retailer(client: TestClient, db):
    user = create_user(db)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}
    retailer = create_retailer(db, user.id)

    update_payload = {
        "name": "변경된 마트 이름",
        "address": "서울시 서초구"
    }

    response = client.put(
        f"/retailers/{retailer.id}",
        json=update_payload,
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["address"] == update_payload["address"]


def test_unauthorized_update_retailer(client: TestClient, db):
    # 정상 유저 + 소매상 생성
    owner = create_user(db)
    retailer = create_retailer(db, owner.id)

    # 다른 유저
    attacker = create_user(db, name="hacker", email_prefix="hacker")
    fake_token, _ = create_token_pair(attacker)
    headers = {"Authorization": f"Bearer {fake_token}"}

    response = client.put(
        f"/retailers/{retailer.id}",
        json={"name": "해커의 시도"},
        headers=headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "해당 소매상 정보를 수정할 권한이 없습니다"


def test_filter_retailers(client: TestClient, db):
    user = create_user(db)
    create_retailer(db, user.id, address="서울시 강남구")

    response = client.get("/retailers/?address=서울시")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any("서울시" in r["address"] for r in data if r.get("address"))