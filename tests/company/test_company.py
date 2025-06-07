from uuid import UUID
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.company import crud, schemas
from app.company.models import Company
from app.wholesaler.models import Wholesaler
from app.user.models import User
from app.core.auth.utils import create_access_token


@pytest.fixture(scope="function")
def test_wholesaler(db: Session, test_user: User):
    wholesaler = Wholesaler(
        user_id=test_user.id,
        name="테스트 도매상",
        phone="010-1234-5678",
        role="owner"
    )
    db.add(wholesaler)
    db.commit()
    db.refresh(wholesaler)
    return wholesaler

@pytest.fixture
def wholesaler_token_headers(test_user):
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def test_company(db, test_wholesaler):
    company = Company(
        name="테스트 회사",
        description="테스트 회사 설명",
        business_number="123-45-67890",
        address="서울시 강남구",
        phone="02-1234-5678",
        email="test@company.com",
        owner=test_wholesaler.user_id
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    # 도매상의 회사 ID 연결
    test_wholesaler.company_id = company.id
    db.commit()
    return company


def test_create_company(client, db: Session, wholesaler_token_headers, test_wholesaler):
    """
    회사 생성 테스트
    """
    company_data = {
        "name": "테스트 회사",
        "description": "테스트 회사 설명",
        "business_number": "123-45-67890",
        "address": "서울시 강남구",
        "phone": "02-1234-5678",
        "email": "test@company.com"
    }
    
    response = client.post(
        "/companies/",
        headers=wholesaler_token_headers,
        json=company_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # 응답 데이터 검증
    
    assert data["name"] == company_data["name"]
    assert data["description"] == company_data["description"]
    assert data["business_number"] == company_data["business_number"]
    assert data["address"] == company_data["address"]
    assert data["phone"] == company_data["phone"]
    assert data["email"] == company_data["email"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    
    # DB에 저장된 데이터 검증
    db_company = db.query(Company).filter(Company.id == UUID(data["id"])).first()
    assert db_company is not None
    assert db_company.name == company_data["name"]
    
    # 도매상 정보 업데이트 검증
    db.expire_all()
    wholesaler = db.query(Wholesaler).filter(Wholesaler.user_id == test_wholesaler.user_id).first()
    assert wholesaler is not None
    assert wholesaler.company_id == UUID(data["id"])
    assert wholesaler.role == "owner"


def test_create_company_duplicate(client, db: Session, wholesaler_token_headers, test_company):
    """
    이미 회사를 소유한 도매상이 회사 생성 시도 시 실패
    """
    company_data = {
        "name": "새로운 회사",
        "description": "새로운 회사 설명",
        "business_number": "987-65-43210",
        "address": "서울시 서초구",
        "phone": "02-9876-5432",
        "email": "new@company.com"
    }
    
    response = client.post(
        "/companies/",
        headers=wholesaler_token_headers,
        json=company_data
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "이미 회사를 소유하고 있습니다"


def test_read_companies(client, db: Session, test_company):
    """
    회사 목록 조회 테스트
    """
    response = client.get("/companies/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert len(data["items"]) > 0
    
    # 검색 기능 테스트
    response = client.get("/companies/?search=테스트")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) > 0


def test_read_company(client, db: Session, test_company):
    """
    회사 상세 조회 테스트
    """
    response = client.get(f"/companies/{test_company.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["id"] == str(test_company.id)
    assert data["name"] == test_company.name
    assert data["description"] == test_company.description
    assert data["business_number"] == test_company.business_number
    assert data["address"] == test_company.address
    assert data["phone"] == test_company.phone
    assert data["email"] == test_company.email


def test_read_company_not_found(client, db: Session):
    """
    존재하지 않는 회사 조회 시 404
    """
    response = client.get("/companies/00000000-0000-0000-0000-000000000000")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_company(client, db: Session, wholesaler_token_headers, test_company):
    """
    회사 정보 수정 테스트
    """
    update_data = {
        "name": "수정된 회사명",
        "description": "수정된 설명",
        "address": "수정된 주소",
        "phone": "02-1111-2222",
        "email": "updated@company.com"
    }
    
    response = client.put(
        f"/companies/{test_company.id}",
        headers=wholesaler_token_headers,
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["address"] == update_data["address"]
    assert data["phone"] == update_data["phone"]
    assert data["email"] == update_data["email"]


def test_update_company_unauthorized(client, db: Session, other_wholesaler_token_headers, test_company):
    """
    권한 없는 도매상이 회사 수정 시도 시 실패
    """
    update_data = {
        "name": "수정된 회사명",
        "description": "수정된 설명"
    }
    
    response = client.put(
        f"/companies/{test_company.id}",
        headers=other_wholesaler_token_headers,
        json=update_data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_read_company_wholesalers(client, db: Session, wholesaler_token_headers, test_company):
    """
    회사 소속 도매상 목록 조회 테스트
    """
    response = client.get(
        f"/companies/{test_company.id}/wholesalers",
        headers=wholesaler_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["company_id"] == str(test_company.id)


def test_read_company_wholesalers_unauthorized(client, db: Session, other_wholesaler_token_headers, test_company):
    """
    권한 없는 도매상이 회사 소속 도매상 목록 조회 시도 시 실패
    """
    response = client.get(
        f"/companies/{test_company.id}/wholesalers",
        headers=other_wholesaler_token_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_read_company_centers(client, db: Session, wholesaler_token_headers, test_company):
    """
    회사 소유 집하장 목록 조회 테스트
    """
    response = client.get(
        f"/companies/{test_company.id}/collection-centers",
        headers=wholesaler_token_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert isinstance(data, list)
    # TODO: 테스트 데이터에 집하장 추가 후 검증 로직 추가 