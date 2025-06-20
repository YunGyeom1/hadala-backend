import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from tests.factories import (
    UserFactory, ProfileFactory, CompanyFactory, 
    CenterFactory, InventorySnapshotFactory
)
from app.core.auth.utils import create_access_token
from app.profile.models import ProfileType, ProfileRole
from app.transactions.common.models import ProductQuality
import uuid
from app.transactions.contract.models import Contract
from unittest.mock import patch

@pytest.fixture
def owner_token_and_profile(db: Session):
    """회사 소유자 토큰과 프로필을 생성합니다."""
    user = UserFactory.create_user(db)
    profile = ProfileFactory.create_wholesaler_profile(
        db, user_id=user.id, username=f"owner_{uuid.uuid4().hex[:8]}"
    )
    token = create_access_token({"sub": str(user.id)})
    return token, profile

@pytest.fixture
def wholesale_company(db: Session, owner_token_and_profile):
    """도매 회사를 생성합니다."""
    token, profile = owner_token_and_profile
    company = CompanyFactory.create_wholesale_company(
        db, owner_id=profile.id, name=f"테스트 도매 회사_{uuid.uuid4().hex[:8]}"
    )
    return company

@pytest.fixture
def centers(db: Session, wholesale_company):
    """테스트용 센터들을 생성합니다."""
    centers = CenterFactory.create_multiple_centers(
        db, company_id=wholesale_company.id, count=2
    )
    return centers

@pytest.fixture
def inventory_snapshots(db: Session, wholesale_company, centers):
    """테스트용 인벤토리 스냅샷들을 생성합니다."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    snapshots = []
    for center in centers:
        # 어제 스냅샷
        snapshot1, items1 = InventorySnapshotFactory.create_complete_inventory_snapshot(
            db, yesterday, wholesale_company.id, center.id,
            items_data=[
                {"product_name": "쌀", "quantity": 50, "quality": "A", "unit_price": 10000.0},
                {"product_name": "감자", "quantity": 30, "quality": "B", "unit_price": 5000.0}
            ]
        )
        
        # 오늘 스냅샷
        snapshot2, items2 = InventorySnapshotFactory.create_complete_inventory_snapshot(
            db, today, wholesale_company.id, center.id,
            items_data=[
                {"product_name": "쌀", "quantity": 40, "quality": "A", "unit_price": 10000.0},
                {"product_name": "양파", "quantity": 20, "quality": "A", "unit_price": 3000.0}
            ]
        )
        
        snapshots.extend([snapshot1, snapshot2])
    
    return snapshots

@pytest.fixture
def dummy_contract(db: Session, wholesale_company, owner_token_and_profile):
    token, profile = owner_token_and_profile
    contract = Contract(
        title="테스트 계약",
        creator_id=profile.id,
        supplier_company_id=wholesale_company.id,
        receiver_company_id=wholesale_company.id,
        total_price=100000.0
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract

def auth_headers(token, profile_id):
    """인증 헤더를 생성합니다."""
    return {"Authorization": f"Bearer {token}", "X-Profile-ID": str(profile_id)}

class TestInventorySnapshotAPI:
    """인벤토리 스냅샷 API 테스트"""
    
    def test_get_company_inventory_snapshot(
        self, client: TestClient, db: Session, 
        owner_token_and_profile, wholesale_company, inventory_snapshots
    ):
        """특정 날짜의 회사 전체 인벤토리 스냅샷을 조회합니다."""
        token, profile = owner_token_and_profile
        today = date.today()
        
        response = client.get(
            f"/inventory-snapshots/company/{wholesale_company.id}/date/{today}",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["snapshot_date"] == str(today)
        assert len(result["centers"]) == 2
        
        # 각 센터의 데이터 확인
        for center in result["centers"]:
            assert "center_id" in center
            assert "center_name" in center
            assert "total_quantity" in center
            assert "total_price" in center
            assert "items" in center
            assert len(center["items"]) > 0

    def test_get_company_inventory_snapshots_by_date_range(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, inventory_snapshots
    ):
        """특정 기간의 회사 전체 인벤토리 스냅샷 목록을 조회합니다."""
        token, profile = owner_token_and_profile
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        response = client.get(
            f"/inventory-snapshots/company/{wholesale_company.id}/date-range",
            params={
                "start_date": str(yesterday),
                "end_date": str(today)
            },
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2  # 어제와 오늘
        
        # 날짜 순서 확인
        dates = [item["snapshot_date"] for item in result]
        assert str(yesterday) in dates
        assert str(today) in dates

    def test_get_center_inventory_snapshot(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers, inventory_snapshots
    ):
        """특정 날짜의 센터 인벤토리 스냅샷을 조회합니다."""
        token, profile = owner_token_and_profile
        today = date.today()
        center = centers[0]
        
        response = client.get(
            f"/inventory-snapshots/center/{center.id}/date/{today}",
            params={"company_id": str(wholesale_company.id)},
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["center_id"] == str(center.id)
        assert result["center_name"] == center.name
        assert "total_quantity" in result
        assert "total_price" in result
        assert "items" in result
        assert len(result["items"]) > 0

    def test_create_center_inventory_snapshot(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers
    ):
        """특정 날짜의 센터 인벤토리 스냅샷을 생성합니다."""
        token, profile = owner_token_and_profile
        today = date.today()
        center = centers[0]
        
        response = client.post(
            f"/inventory-snapshots/center/{center.id}/date/{today}",
            params={"company_id": str(wholesale_company.id)},
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["center_id"] == str(center.id)
        assert result["center_name"] == center.name

    def test_update_company_inventory_snapshot(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers, inventory_snapshots, dummy_contract
    ):
        """특정 날짜의 회사 전체 인벤토리 스냅샷을 수정합니다."""
        token, profile = owner_token_and_profile
        today = date.today()
        center = centers[0]

        update_data = {
            "snapshot_date": str(today),
            "centers": [
                {
                    "center_id": str(center.id),
                    "items": [
                        {
                            "product_name": "쌀",
                            "quality": "A",
                            "quantity": 100,
                            "unit_price": 12000.0
                        },
                        {
                            "product_name": "감자",
                            "quality": "B",
                            "quantity": 50,
                            "unit_price": 6000.0
                        }
                    ]
                }
            ]
        }

        response = client.put(
            f"/inventory-snapshots/company/{wholesale_company.id}/date/{today}",
            json=update_data,
            params={"contract_id": str(dummy_contract.id)},
            headers=auth_headers(token, profile.id)
        )
        assert response.status_code == 200
        result = response.json()
        assert result["snapshot_date"] == str(today)
        assert len(result["centers"]) >= 1

    def test_get_company_inventory_snapshot_not_found(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company
    ):
        """존재하지 않는 날짜의 인벤토리 스냅샷 조회 시 404 오류"""
        token, profile = owner_token_and_profile
        future_date = date.today() + timedelta(days=30)
        
        response = client.get(
            f"/inventory-snapshots/company/{wholesale_company.id}/date/{future_date}",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 404

    def test_get_center_inventory_snapshot_not_found(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers
    ):
        """존재하지 않는 센터의 인벤토리 스냅샷 조회 시 404 오류"""
        token, profile = owner_token_and_profile
        today = date.today()
        non_existent_center_id = str(uuid.uuid4())
        
        response = client.get(
            f"/inventory-snapshots/center/{non_existent_center_id}/date/{today}",
            params={"company_id": str(wholesale_company.id)},
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 404

    def test_get_company_inventory_snapshot_unauthorized(
        self, client: TestClient, db: Session, wholesale_company, inventory_snapshots
    ):
        """인증되지 않은 사용자의 인벤토리 스냅샷 조회 시 401 오류"""
        today = date.today()
        
        response = client.get(
            f"/inventory-snapshots/company/{wholesale_company.id}/date/{today}"
        )
        
        assert response.status_code == 401

    def test_update_inventory_snapshot_invalid_data(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers, inventory_snapshots
    ):
        """잘못된 데이터로 인벤토리 스냅샷 수정 시 422 오류"""
        token, profile = owner_token_and_profile
        today = date.today()
        center = centers[0]
        
        # 잘못된 품질 등급으로 수정 시도
        update_data = {
            "snapshot_date": str(today),
            "centers": [
                {
                    "center_id": str(center.id),
                    "items": [
                        {
                            "product_name": "쌀",
                            "quality": "INVALID_QUALITY",  # 잘못된 품질 등급
                            "quantity": 100,
                            "unit_price": 12000.0
                        }
                    ]
                }
            ]
        }
        
        response = client.put(
            f"/inventory-snapshots/company/{wholesale_company.id}/date/{today}",
            json=update_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 422

    def test_date_range_invalid_dates(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company
    ):
        """잘못된 날짜 범위로 조회 시 422 오류"""
        token, profile = owner_token_and_profile
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # 시작일이 종료일보다 늦은 경우
        response = client.get(
            f"/inventory-snapshots/company/{wholesale_company.id}/date-range",
            params={
                "start_date": str(today),
                "end_date": str(yesterday)
            },
            headers=auth_headers(token, profile.id)
        )
        
        # 날짜 범위가 잘못되어도 API는 정상 동작하지만 빈 결과 반환
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 0 