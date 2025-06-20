import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.auth.utils import create_access_token
from app.profile.models import ProfileRole, ProfileType
from app.company.common.models import CompanyType
from tests.factories import UserFactory, ProfileFactory, CompanyFactory
import uuid

@pytest.fixture
def owner_token_and_profile(db: Session):
    user = UserFactory.create_user(db)
    profile = ProfileFactory.create_profile(
        db, 
        user_id=user.id, 
        type=ProfileType.wholesaler, 
        role=ProfileRole.owner,
        username=f"owner_{uuid.uuid4().hex[:8]}"
    )
    token = create_access_token({"sub": str(user.id)})
    return token, profile

@pytest.fixture
def wholesale_company(db: Session, owner_token_and_profile):
    _, profile = owner_token_and_profile
    company = CompanyFactory.create_company(
        db, 
        name="도매회사", 
        type=CompanyType.wholesaler, 
        owner_id=profile.id
    )
    profile.company_id = company.id
    db.commit()
    return company

@pytest.fixture
def retail_company(db: Session, owner_token_and_profile):
    _, profile = owner_token_and_profile
    company = CompanyFactory.create_company(
        db, 
        name="소매회사", 
        type=CompanyType.retailer, 
        owner_id=profile.id
    )
    profile.company_id = company.id
    db.commit()
    return company

@pytest.fixture
def farmer_company(db: Session, owner_token_and_profile):
    _, profile = owner_token_and_profile
    company = CompanyFactory.create_company(
        db, 
        name="농장", 
        type=CompanyType.farmer, 
        owner_id=profile.id
    )
    profile.company_id = company.id
    db.commit()
    return company

def auth_headers(token, profile_id):
    return {
        "Authorization": f"Bearer {token}",
        "X-Profile-ID": str(profile_id)
    }

# Wholesale Company Detail Tests
def test_create_wholesale_company_detail(client: TestClient, db: Session, owner_token_and_profile, wholesale_company):
    token, profile = owner_token_and_profile
    data = {
        "address": "서울시 강남구",
        "region": "강남",
        "latitude": 37.5665,
        "longitude": 126.9780,
        "description": "도매회사 상세 정보",
        "phone": "02-1234-5678",
        "email": "wholesale@example.com",
        "representative": "김도매",
        "business_registration_number": "123-45-67890",
        "established_year": 2020,
        "monthly_transaction_volume": 1000000.0,
        "daily_transport_capacity": 5000.0,
        "main_products": "쌀,감자,양파",
        "has_cold_storage": True,
        "number_of_vehicles": 10
    }
    response = client.post(f"/companies/wholesale/{wholesale_company.id}/detail", json=data, headers=auth_headers(token, profile.id))
    assert response.status_code == 200
    result = response.json()
    assert result["address"] == "서울시 강남구"
    assert result["monthly_transaction_volume"] == 1000000.0
    assert result["has_cold_storage"] == True

def test_get_wholesale_company_detail(client: TestClient, db: Session, owner_token_and_profile, wholesale_company):
    token, profile = owner_token_and_profile
    # 먼저 상세 정보 생성
    data = {
        "address": "서울시 강남구",
        "monthly_transaction_volume": 1000000.0,
        "has_cold_storage": True
    }
    create_response = client.post(f"/companies/wholesale/{wholesale_company.id}/detail", json=data, headers=auth_headers(token, profile.id))
    assert create_response.status_code == 200
    
    # 조회
    response = client.get(f"/companies/wholesale/{wholesale_company.id}/detail")
    assert response.status_code == 200
    result = response.json()
    assert result["address"] == "서울시 강남구"
    assert result["monthly_transaction_volume"] == 1000000.0

def test_update_wholesale_company_detail(client: TestClient, db: Session, owner_token_and_profile, wholesale_company):
    token, profile = owner_token_and_profile
    # 먼저 상세 정보 생성
    data = {
        "address": "서울시 강남구",
        "monthly_transaction_volume": 1000000.0
    }
    create_response = client.post(f"/companies/wholesale/{wholesale_company.id}/detail", json=data, headers=auth_headers(token, profile.id))
    assert create_response.status_code == 200
    
    # 수정
    update_data = {
        "address": "서울시 서초구",
        "monthly_transaction_volume": 2000000.0,
        "has_cold_storage": True
    }
    response = client.put(f"/companies/wholesale/{wholesale_company.id}/detail", json=update_data, headers=auth_headers(token, profile.id))
    assert response.status_code == 200
    result = response.json()
    assert result["address"] == "서울시 서초구"
    assert result["monthly_transaction_volume"] == 2000000.0
    assert result["has_cold_storage"] == True

# Retail Company Detail Tests
def test_create_retail_company_detail(client: TestClient, db: Session, owner_token_and_profile, retail_company):
    token, profile = owner_token_and_profile
    data = {
        "address": "서울시 마포구",
        "region": "마포",
        "latitude": 37.5665,
        "longitude": 126.9780,
        "description": "소매회사 상세 정보",
        "phone": "02-9876-5432",
        "email": "retail@example.com",
        "representative": "이소매",
        "business_registration_number": "987-65-43210",
        "established_year": 2021
    }
    response = client.post(f"/companies/retail/{retail_company.id}/detail", json=data, headers=auth_headers(token, profile.id))
    assert response.status_code == 200
    result = response.json()
    assert result["address"] == "서울시 마포구"
    assert result["region"] == "마포"
    assert result["phone"] == "02-9876-5432"

def test_get_retail_company_detail(client: TestClient, db: Session, owner_token_and_profile, retail_company):
    token, profile = owner_token_and_profile
    # 먼저 상세 정보 생성
    data = {
        "address": "서울시 마포구",
        "region": "마포"
    }
    create_response = client.post(f"/companies/retail/{retail_company.id}/detail", json=data, headers=auth_headers(token, profile.id))
    assert create_response.status_code == 200
    
    # 조회
    response = client.get(f"/companies/retail/{retail_company.id}/detail")
    assert response.status_code == 200
    result = response.json()
    assert result["address"] == "서울시 마포구"
    assert result["region"] == "마포"

def test_update_retail_company_detail(client: TestClient, db: Session, owner_token_and_profile, retail_company):
    token, profile = owner_token_and_profile
    # 먼저 상세 정보 생성
    data = {
        "address": "서울시 마포구"
    }
    create_response = client.post(f"/companies/retail/{retail_company.id}/detail", json=data, headers=auth_headers(token, profile.id))
    assert create_response.status_code == 200
    
    # 수정
    update_data = {
        "address": "서울시 영등포구",
        "region": "영등포"
    }
    response = client.put(f"/companies/retail/{retail_company.id}/detail", json=update_data, headers=auth_headers(token, profile.id))
    assert response.status_code == 200
    result = response.json()
    assert result["address"] == "서울시 영등포구"
    assert result["region"] == "영등포"

# Farmer Company Detail Tests
def test_create_farmer_company_detail(client: TestClient, db: Session, owner_token_and_profile, farmer_company):
    token, profile = owner_token_and_profile
    data = {
        "address": "경기도 수원시",
        "region": "수원",
        "latitude": 37.2636,
        "longitude": 127.0286,
        "description": "농장 상세 정보",
        "phone": "031-123-4567",
        "email": "farmer@example.com",
        "representative": "박농부",
        "business_registration_number": "456-78-90123",
        "established_year": 2019
    }
    response = client.post(f"/companies/farmer/{farmer_company.id}/detail", json=data, headers=auth_headers(token, profile.id))
    assert response.status_code == 200
    result = response.json()
    assert result["address"] == "경기도 수원시"
    assert result["region"] == "수원"
    assert result["phone"] == "031-123-4567"

def test_get_farmer_company_detail(client: TestClient, db: Session, owner_token_and_profile, farmer_company):
    token, profile = owner_token_and_profile
    # 먼저 상세 정보 생성
    data = {
        "address": "경기도 수원시",
        "region": "수원"
    }
    create_response = client.post(f"/companies/farmer/{farmer_company.id}/detail", json=data, headers=auth_headers(token, profile.id))
    assert create_response.status_code == 200
    
    # 조회
    response = client.get(f"/companies/farmer/{farmer_company.id}/detail")
    assert response.status_code == 200
    result = response.json()
    assert result["address"] == "경기도 수원시"
    assert result["region"] == "수원"

def test_update_farmer_company_detail(client: TestClient, db: Session, owner_token_and_profile, farmer_company):
    token, profile = owner_token_and_profile
    # 먼저 상세 정보 생성
    data = {
        "address": "경기도 수원시"
    }
    create_response = client.post(f"/companies/farmer/{farmer_company.id}/detail", json=data, headers=auth_headers(token, profile.id))
    assert create_response.status_code == 200
    
    # 수정
    update_data = {
        "address": "경기도 용인시",
        "region": "용인"
    }
    response = client.put(f"/companies/farmer/{farmer_company.id}/detail", json=update_data, headers=auth_headers(token, profile.id))
    assert response.status_code == 200
    result = response.json()
    assert result["address"] == "경기도 용인시"
    assert result["region"] == "용인"

# Error Cases
def test_create_detail_no_permission(client: TestClient, db: Session, wholesale_company):
    # 다른 사용자가 생성 시도
    other_user = UserFactory.create_user(db)
    other_profile = ProfileFactory.create_profile(
        db, 
        user_id=other_user.id, 
        type=ProfileType.wholesaler, 
        role=ProfileRole.owner,
        username=f"other_{uuid.uuid4().hex[:8]}"
    )
    token = create_access_token({"sub": str(other_user.id)})
    
    data = {"address": "무단 접근"}
    response = client.post(f"/companies/wholesale/{wholesale_company.id}/detail", json=data, headers=auth_headers(token, other_profile.id))
    assert response.status_code == 403

def test_get_detail_not_found(client: TestClient, db: Session, wholesale_company):
    response = client.get(f"/companies/wholesale/{wholesale_company.id}/detail")
    assert response.status_code == 404
    assert "상세 정보를 찾을 수 없습니다" in response.json()["detail"] 