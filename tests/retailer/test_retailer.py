import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from app.user.models import User
from app.retailer.models import Retailer
from app.core.auth.utils import create_access_token


@pytest.fixture
def retailer_payload():
    return {
        "name": "홍길동 마트",
        "address": "서울시 강남구",
        "description": "신선식품 전문 마트"
    }


@pytest.fixture
def auth_headers(test_user: User):
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


def test_create_retailer(client: TestClient, test_user: User, auth_headers: dict, db, retailer_payload):
    response = client.post("/retailers/", json=retailer_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == retailer_payload["name"]
    assert data["address"] == retailer_payload["address"]
    assert data["description"] == retailer_payload["description"]
    assert "id" in data
    assert "created_at" in data
    assert data["user_id"] == str(test_user.id)


def test_create_retailer_duplicate(client: TestClient, test_user: User, auth_headers: dict, db, retailer_payload):
    # 첫 번째 생성
    response = client.post("/retailers/", json=retailer_payload, headers=auth_headers)
    assert response.status_code == 200

    # 두 번째 생성 시도
    response = client.post("/retailers/", json=retailer_payload, headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "이미 소매상으로 등록된 사용자입니다"


def test_get_retailer(client: TestClient, test_retailer: Retailer, auth_headers: dict):
    response = client.get(f"/retailers/{test_retailer.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_retailer.id)
    assert data["name"] == test_retailer.name


def test_update_retailer(client: TestClient, test_retailer: Retailer, test_user: User, auth_headers: dict):
    update_payload = {
        "name": "변경된 마트 이름",
        "address": "서울시 서초구"
    }
    response = client.put(
        f"/retailers/{test_retailer.id}",
        json=update_payload,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["address"] == update_payload["address"]


def test_unauthorized_update_retailer(client: TestClient, test_retailer: Retailer, db):
    # 다른 유저 생성
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
        f"/retailers/{test_retailer.id}",
        json={"name": "해커의 시도"},
        headers=headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "해당 소매상 정보를 수정할 권한이 없습니다"


def test_filter_retailers(client: TestClient, test_retailer: Retailer):
    response = client.get("/retailers/?address=서울시")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any("서울시" in retailer["address"] for retailer in data if retailer["address"])