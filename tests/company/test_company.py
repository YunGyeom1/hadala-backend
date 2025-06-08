import pytest
from uuid import UUID
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.factories import (
    create_user,
    create_token_pair,
    create_wholesaler,
    create_company,
)

@pytest.fixture
def test_setup(db: Session, client: TestClient):
    user = create_user(db)
    wholesaler = create_wholesaler(db, user)
    company = create_company(db, user.id)
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}
    return {
        "db": db,
        "client": client,
        "user": user,
        "wholesaler": wholesaler,
        "company": company,
        "headers": headers,
    }

def test_create_company(client: TestClient, db: Session):
    # 1. 유저 및 도매상 생성
    user = create_user(db)
    create_wholesaler(db, user)

    # 2. 인증 토큰 생성
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    # 3. 회사 생성 요청
    company_data = {
        "name": "테스트 회사",
        "description": "테스트 회사 설명",
        "business_number": "123-45-67890",
        "address": "서울시 강남구",
        "phone": "02-1234-5678",
        "email": f"testre@company.com",  # 유니크 보장
    }

    response = client.post("/companies/", headers=headers, json=company_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # 4. 응답 검증
    assert data["name"] == company_data["name"]
    assert data["business_number"] == company_data["business_number"]

    # 5. DB 확인
    from app.company.models import Company
    from app.wholesaler.models import Wholesaler

    db.expire_all()
    db_company = db.query(Company).filter(Company.id == UUID(data["id"])).first()
    assert db_company.name == company_data["name"]

    db_wholesaler = db.query(Wholesaler).filter(Wholesaler.user_id == user.id).first()
    assert db_wholesaler.company_id == UUID(data["id"])
    assert db_wholesaler.role == "owner"

def test_create_company_duplicate(test_setup):
    client, headers = test_setup["client"], test_setup["headers"]
    company_data = {
        "name": "새로운 회사",
        "description": "새로운 회사 설명",
        "business_number": "987-65-43210",
        "address": "서울시 서초구",
        "phone": "02-9876-5432",
        "email": "new@company.com"
    }
    response = client.post("/companies/", headers=headers, json=company_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_read_companies(test_setup):
    client = test_setup["client"]
    response = client.get("/companies/")
    assert response.status_code == status.HTTP_200_OK
    assert "items" in response.json()

def test_read_company(test_setup):
    client = test_setup["client"]
    company = test_setup["company"]
    response = client.get(f"/companies/{company.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(company.id)

def test_read_company_not_found(client: TestClient):
    response = client.get("/companies/00000000-0000-0000-0000-000000000000")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_company(test_setup):
    client, company, headers = test_setup["client"], test_setup["company"], test_setup["headers"]
    update_data = {
        "name": "수정된 회사명",
        "description": "수정된 설명",
        "address": "수정된 주소",
        "phone": "02-1111-2222",
        "email": "updated@company.com"
    }
    response = client.put(f"/companies/{company.id}", headers=headers, json=update_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == update_data["name"]

def test_update_company_unauthorized(db: Session, client: TestClient):
    owner = create_user(db)
    owner_wholesaler = create_wholesaler(db, owner)
    company = create_company(db, owner.id)

    attacker = create_user(db, name="hacker", email_prefix="hacker")
    create_wholesaler(db, attacker, role="staff")
    token, _ = create_token_pair(attacker)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(f"/companies/{company.id}", headers=headers, json={"name": "해커"})
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_read_company_wholesalers(test_setup):
    client, company, headers = test_setup["client"], test_setup["company"], test_setup["headers"]
    response = client.get(f"/companies/{company.id}/wholesalers", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) > 0

def test_read_company_wholesalers_unauthorized(db: Session, client: TestClient):
    owner = create_user(db)
    create_wholesaler(db, owner)
    company = create_company(db, owner.id)

    attacker = create_user(db, name="hacker", email_prefix="hacker")
    create_wholesaler(db, attacker)
    token, _ = create_token_pair(attacker)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/companies/{company.id}/wholesalers", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_read_company_centers(test_setup):
    client, company, headers = test_setup["client"], test_setup["company"], test_setup["headers"]
    response = client.get(f"/companies/{company.id}/centers", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)