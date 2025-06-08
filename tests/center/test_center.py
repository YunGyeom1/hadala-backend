import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.center.models import Center
from tests.factories import create_user, create_token_pair, create_company, create_wholesaler, create_center

def test_create_center(client: TestClient, db: Session):
    user = create_user(db)
    wholesaler = create_wholesaler(db, user, role="owner")
    company = create_company(db, user.id)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    payload = {
        "name": "중앙집하장",
        "address": "서울시 중구",
        "company_id": str(company.id)
    }

    response = client.post("/centers", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["address"] == payload["address"]
    assert data["company_id"] == str(company.id)

def test_get_center(client: TestClient, db: Session):
    user = create_user(db)
    wholesaler = create_wholesaler(db, user, role="owner")
    company = create_company(db, user.id)
    center = create_center(db, name="수원센터", company_id=company.id)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.get(f"/centers/{center.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(center.id)
    assert data["name"] == center.name

def test_update_center(client: TestClient, db: Session):
    user = create_user(db)
    wholesaler = create_wholesaler(db, user, role="owner")
    company = create_company(db, user.id)
    center = create_center(db, name="기존 이름", company_id=company.id)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    update_payload = {
        "name": "변경된 이름",
        "address": "부산시 해운대구"
    }

    response = client.put(f"/centers/{center.id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_payload["name"]
    assert data["address"] == update_payload["address"]

def test_delete_center(client: TestClient, db: Session):
    user = create_user(db)
    wholesaler = create_wholesaler(db, user, role="owner")
    company = create_company(db, user.id)
    center = create_center(db, company_id=company.id)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.delete(f"/centers/{center.id}", headers=headers)
    assert response.status_code == 204

    # 삭제 후 접근 시 403 또는 404
    get_response = client.get(f"/centers/{center.id}", headers=headers)
    assert get_response.status_code in [403, 404]

def test_list_centers(client: TestClient, db: Session):
    user = create_user(db)
    wholesaler = create_wholesaler(db, user)
    company = create_company(db, user.id)
    create_center(db, name="센터1", company_id=company.id)
    create_center(db, name="센터2", company_id=company.id)

    response = client.get("/centers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2