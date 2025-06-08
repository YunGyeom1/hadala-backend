import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
from uuid import UUID

from app.main import app
from app.database.session import get_db
from tests.factories import (
    create_user, create_wholesaler, create_company, create_farmer, create_center,
    create_wholesale_contract, create_wholesale_contract_item, create_token_pair
)

client = TestClient(app)

@pytest.fixture
def test_setup(db: Session, client: TestClient):
    """테스트에 필요한 기본 데이터를 생성합니다."""
    # 사용자 생성
    user = create_user(db)
    
    # 도매상 생성
    wholesaler = create_wholesaler(db, user=user)
    
    # 회사 생성
    company = create_company(db, user.id)
    
    # 농가 생성
    farmer = create_farmer(db)
    
    # 수집 센터 생성
    center = create_center(db, company_id=company.id)
    
    # 토큰 생성
    access_token, _ = create_token_pair(user)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    return {
        "user": user,
        "wholesaler": wholesaler,
        "company": company,
        "farmer": farmer,
        "center": center,
        "headers": headers
    }

def test_create_contract(test_setup, db: Session):
    """새 계약 생성 테스트"""
    contract_data = {
        "center_id": str(test_setup["center"].id),
        "company_id": str(test_setup["company"].id), 
        "wholesaler_id": str(test_setup["wholesaler"].id),
        "farmer_id": str(test_setup["farmer"].id),
        "contract_date": date.today().isoformat(),
        "shipment_date": (date.today() + timedelta(days=7)).isoformat(),
        "note": "테스트 계약",
        "total_price": 500000.0,
        "items": [
            {
                "crop_name": "사과",
                "quantity_kg": 100.0,
                "unit_price": 5000.0,
                "quality_required": "A",
                "total_price": 500000.0
                
            }
        ]
    }
    
    response = client.post(
        "/wholesale-contracts/",
        json=contract_data,
        headers=test_setup["headers"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["center_id"] == str(test_setup["center"].id)
    assert data["farmer_id"] == str(test_setup["farmer"].id)
    assert len(data["items"]) == 1
    assert data["items"][0]["crop_name"] == "사과"

def test_get_contracts(test_setup, db: Session):
    """계약 목록 조회 테스트"""
    # 먼저 계약 생성
    contract = create_wholesale_contract(
        db,
        center_id=test_setup["center"].id,
        wholesaler_id=test_setup["wholesaler"].id,
        farmer_id=test_setup["farmer"].id,
        company_id=test_setup["company"].id
    )
    
    create_wholesale_contract_item(
        db,
        contract_id=contract.id
    )
    
    # 계약 목록 조회
    response = client.get(
        "/wholesale-contracts/",
        headers=test_setup["headers"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["center_id"] == str(test_setup["center"].id)

def test_get_contract(test_setup, db: Session):
    """특정 계약 조회 테스트"""
    # 먼저 계약 생성
    contract = create_wholesale_contract(
        db,
        center_id=test_setup["center"].id,
        wholesaler_id=test_setup["wholesaler"].id,
        farmer_id=test_setup["farmer"].id,
        company_id=test_setup["company"].id
    )
    
    create_wholesale_contract_item(
        db,
        contract_id=contract.id
    )
    
    # 특정 계약 조회
    response = client.get(
        f"/wholesale-contracts/{contract.id}",
        headers=test_setup["headers"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(contract.id)
    assert data["center_id"] == str(test_setup["center"].id)

def test_update_contract(test_setup, db: Session):
    """계약 정보 업데이트 테스트"""
    # 먼저 계약 생성
    contract = create_wholesale_contract(
        db,
        center_id=test_setup["center"].id,
        wholesaler_id=test_setup["wholesaler"].id,
        farmer_id=test_setup["farmer"].id,
        company_id=test_setup["company"].id
    )
    
    create_wholesale_contract_item(
        db,
        contract_id=contract.id
    )
    
    # 계약 정보 업데이트
    update_data = {
        "note": "업데이트된 테스트 계약",
        "shipment_date": (date.today() + timedelta(days=14)).isoformat()
    }
    
    response = client.put(
        f"/wholesale-contracts/{contract.id}",
        json=update_data,
        headers=test_setup["headers"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["note"] == "업데이트된 테스트 계약"

def test_delete_contract(test_setup, db: Session):
    """계약 삭제 테스트"""
    # 먼저 계약 생성
    contract = create_wholesale_contract(
        db,
        center_id=test_setup["center"].id,
        wholesaler_id=test_setup["wholesaler"].id,
        farmer_id=test_setup["farmer"].id,
        company_id=test_setup["company"].id
    )
    
    create_wholesale_contract_item(
        db,
        contract_id=contract.id
    )
    
    # 계약 삭제
    response = client.delete(
        f"/wholesale-contracts/{contract.id}",
        headers=test_setup["headers"]
    )
    
    assert response.status_code == 200
    
    # 삭제된 계약 조회 시도
    get_response = client.get(
        f"/wholesale-contracts/{contract.id}",
        headers=test_setup["headers"]
    )
    assert get_response.status_code == 404

def test_contract_status_flow(test_setup, db: Session):
    """계약 상태 변경 흐름 테스트"""
    # 먼저 계약 생성
    contract = create_wholesale_contract(
        db,
        center_id=test_setup["center"].id,
        wholesaler_id=test_setup["wholesaler"].id,
        farmer_id=test_setup["farmer"].id,
        company_id=test_setup["company"].id
    )
    
    create_wholesale_contract_item(
        db,
        contract_id=contract.id
    )
    
    # 계약 확정
    confirm_response = client.post(
        f"/wholesale-contracts/{contract.id}/confirm",
        headers=test_setup["headers"]
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["contract_status"] == "confirmed"
    
    # 계약 완료
    complete_response = client.post(
        f"/wholesale-contracts/{contract.id}/complete",
        headers=test_setup["headers"]
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["contract_status"] == "completed"

def test_contract_items(test_setup, db: Session):
    """계약 품목 관련 테스트"""
    # 먼저 계약 생성
    contract = create_wholesale_contract(
        db,
        center_id=test_setup["center"].id,
        wholesaler_id=test_setup["wholesaler"].id,
        farmer_id=test_setup["farmer"].id,
        company_id=test_setup["company"].id
    )
    
    item = create_wholesale_contract_item(
        db,
        contract_id=contract.id
    )
    
    # 계약 품목 목록 조회
    items_response = client.get(
        f"/wholesale-contracts/{contract.id}/items",
        headers=test_setup["headers"]
    )
    assert items_response.status_code == 200
    assert len(items_response.json()) == 1
    
    # 계약 품목 수정
    update_data = {
        "quantity_kg": 150.0,
        "unit_price": 5500.0
    }
    update_response = client.put(
        f"/wholesale-contracts/items/{item.id}",
        json=update_data,
        headers=test_setup["headers"]
    )
    assert update_response.status_code == 200
    assert update_response.json()["quantity_kg"] == 150.0
    
    # 계약 품목 삭제
    delete_response = client.delete(
        f"/wholesale-contracts/items/{item.id}",
        headers=test_setup["headers"]
    )
    assert delete_response.status_code == 200
    
    # 삭제 후 품목 목록 조회
    items_response = client.get(
        f"/wholesale-contracts/{contract.id}/items",
        headers=test_setup["headers"]
    )
    assert items_response.status_code == 200
    assert len(items_response.json()) == 0 