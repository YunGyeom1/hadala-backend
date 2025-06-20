import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from tests.factories import (
    UserFactory, ProfileFactory, CompanyFactory, CenterFactory
)
from app.core.auth.utils import create_access_token
from app.profile.models import ProfileType, ProfileRole
from app.transactions.common.models import ContractStatus, PaymentStatus, ProductQuality
import uuid

@pytest.fixture
def supplier_token_and_profile(db: Session):
    """공급자 토큰과 프로필을 생성합니다."""
    user = UserFactory.create_user(db)
    profile = ProfileFactory.create_wholesaler_profile(
        db, user_id=user.id, username=f"supplier_{uuid.uuid4().hex[:8]}"
    )
    token = create_access_token({"sub": str(user.id)})
    return token, profile

@pytest.fixture
def receiver_token_and_profile(db: Session):
    """수신자 토큰과 프로필을 생성합니다."""
    user = UserFactory.create_user(db)
    profile = ProfileFactory.create_wholesaler_profile(
        db, user_id=user.id, username=f"receiver_{uuid.uuid4().hex[:8]}"
    )
    token = create_access_token({"sub": str(user.id)})
    return token, profile

@pytest.fixture
def supplier_company(db: Session, supplier_token_and_profile):
    """공급자 회사를 생성합니다."""
    token, profile = supplier_token_and_profile
    company = CompanyFactory.create_wholesale_company(
        db, owner_id=profile.id, name=f"공급자 회사_{uuid.uuid4().hex[:8]}"
    )
    
    # 프로필의 company_id를 설정
    profile.company_id = company.id
    db.commit()
    db.refresh(profile)
    
    return company

@pytest.fixture
def receiver_company(db: Session, receiver_token_and_profile):
    """수신자 회사를 생성합니다."""
    token, profile = receiver_token_and_profile
    company = CompanyFactory.create_wholesale_company(
        db, owner_id=profile.id, name=f"수신자 회사_{uuid.uuid4().hex[:8]}"
    )
    
    # 프로필의 company_id를 설정
    profile.company_id = company.id
    db.commit()
    db.refresh(profile)
    
    return company

@pytest.fixture
def centers(db: Session, supplier_company, receiver_company):
    """테스트용 센터들을 생성합니다."""
    supplier_centers = CenterFactory.create_multiple_centers(
        db, company_id=supplier_company.id, count=2
    )
    receiver_centers = CenterFactory.create_multiple_centers(
        db, company_id=receiver_company.id, count=2
    )
    return supplier_centers + receiver_centers

def auth_headers(token, profile_id):
    """인증 헤더를 생성합니다."""
    return {"Authorization": f"Bearer {token}", "X-Profile-ID": str(profile_id)}

class TestContractAPI:
    """계약 API 테스트"""
    
    def test_create_contract_success(
        self, client: TestClient, db: Session,
        supplier_token_and_profile, supplier_company, receiver_company, centers
    ):
        """계약 생성 성공 테스트"""
        token, profile = supplier_token_and_profile
        supplier_center = centers[0]  # 공급자 센터
        receiver_center = centers[2]  # 수신자 센터
        
        contract_data = {
            "title": "테스트 계약",
            "notes": "테스트 계약입니다.",
            "supplier_company_id": str(supplier_company.id),
            "receiver_company_id": str(receiver_company.id),
            "departure_center_id": str(supplier_center.id),
            "arrival_center_id": str(receiver_center.id),
            "contract_datetime": datetime.now().isoformat(),
            "delivery_datetime": (datetime.now() + timedelta(days=7)).isoformat(),
            "payment_due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "contract_status": ContractStatus.DRAFT.value,
            "payment_status": PaymentStatus.UNPAID.value,
            "items": [
                {
                    "contract_id": str(uuid.uuid4()),  # 임시 ID
                    "product_name": "쌀",
                    "quality": ProductQuality.A.value,
                    "quantity": 100,
                    "unit_price": 10000.0,
                    "total_price": 1000000.0
                },
                {
                    "contract_id": str(uuid.uuid4()),  # 임시 ID
                    "product_name": "감자",
                    "quality": ProductQuality.B.value,
                    "quantity": 50,
                    "unit_price": 5000.0,
                    "total_price": 250000.0
                }
            ]
        }
        
        response = client.post(
            "/contracts/",
            json=contract_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "테스트 계약"
        assert result["supplier_company_id"] == str(supplier_company.id)
        assert result["receiver_company_id"] == str(receiver_company.id)
        assert len(result["items"]) == 2
        assert result["total_price"] == 1250000.0

    def test_create_contract_no_permission(
        self, client: TestClient, db: Session,
        supplier_token_and_profile, supplier_company, receiver_company, centers
    ):
        """권한이 없는 사용자의 계약 생성 시 403 오류"""
        # member 역할로 프로필 생성
        user = UserFactory.create_user(db)
        member_profile = ProfileFactory.create_wholesaler_profile(
            db,
            user_id=user.id,
            username=f"member_{uuid.uuid4().hex[:8]}",
            company_id=supplier_company.id,
            role=ProfileRole.member
        )
        
        token = create_access_token({"sub": str(user.id)})
        supplier_center = centers[0]
        receiver_center = centers[2]
        
        contract_data = {
            "title": "권한 없는 계약",
            "supplier_company_id": str(supplier_company.id),
            "receiver_company_id": str(receiver_company.id),
            "departure_center_id": str(supplier_center.id),
            "arrival_center_id": str(receiver_center.id),
            "items": [
                {
                    "contract_id": str(uuid.uuid4()),
                    "product_name": "쌀",
                    "quality": ProductQuality.A.value,
                    "quantity": 100,
                    "unit_price": 10000.0,
                    "total_price": 1000000.0
                }
            ]
        }
        
        response = client.post(
            "/contracts/",
            json=contract_data,
            headers=auth_headers(token, member_profile.id)
        )
        
        assert response.status_code == 403
        assert "Required roles" in response.json()["detail"]

    def test_get_contract_success(
        self, client: TestClient, db: Session,
        supplier_token_and_profile, supplier_company, receiver_company, centers
    ):
        """계약 조회 성공 테스트"""
        token, profile = supplier_token_and_profile
        supplier_center = centers[0]
        receiver_center = centers[2]
        
        # 먼저 계약 생성
        contract_data = {
            "title": "조회 테스트 계약",
            "supplier_company_id": str(supplier_company.id),
            "receiver_company_id": str(receiver_company.id),
            "departure_center_id": str(supplier_center.id),
            "arrival_center_id": str(receiver_center.id),
            "items": [
                {
                    "contract_id": str(uuid.uuid4()),
                    "product_name": "쌀",
                    "quality": ProductQuality.A.value,
                    "quantity": 100,
                    "unit_price": 10000.0,
                    "total_price": 1000000.0
                }
            ]
        }
        
        create_response = client.post(
            "/contracts/",
            json=contract_data,
            headers=auth_headers(token, profile.id)
        )
        assert create_response.status_code == 201
        contract_id = create_response.json()["id"]
        
        # 계약 조회
        response = client.get(
            f"/contracts/{contract_id}",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == contract_id
        assert result["title"] == "조회 테스트 계약"
        assert len(result["items"]) == 1

    def test_get_contract_not_found(
        self, client: TestClient, db: Session,
        supplier_token_and_profile
    ):
        """존재하지 않는 계약 조회 시 404 오류"""
        token, profile = supplier_token_and_profile
        non_existent_contract_id = str(uuid.uuid4())
        
        response = client.get(
            f"/contracts/{non_existent_contract_id}",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 404
        assert "Contract not found" in response.json()["detail"]

    def test_get_contract_no_permission(
        self, client: TestClient, db: Session,
        supplier_token_and_profile, supplier_company, receiver_company, centers
    ):
        """권한이 없는 사용자의 계약 조회 시 403 오류"""
        token, profile = supplier_token_and_profile
        supplier_center = centers[0]
        receiver_center = centers[2]
        
        # 먼저 계약 생성
        contract_data = {
            "title": "권한 테스트 계약",
            "supplier_company_id": str(supplier_company.id),
            "receiver_company_id": str(receiver_company.id),
            "departure_center_id": str(supplier_center.id),
            "arrival_center_id": str(receiver_center.id),
            "items": [
                {
                    "contract_id": str(uuid.uuid4()),
                    "product_name": "쌀",
                    "quality": ProductQuality.A.value,
                    "quantity": 100,
                    "unit_price": 10000.0,
                    "total_price": 1000000.0
                }
            ]
        }
        
        create_response = client.post(
            "/contracts/",
            json=contract_data,
            headers=auth_headers(token, profile.id)
        )
        assert create_response.status_code == 201
        contract_id = create_response.json()["id"]
        
        # 다른 회사의 사용자로 조회 시도
        other_user = UserFactory.create_user(db)
        other_company = CompanyFactory.create_wholesale_company(
            db, name=f"다른 회사_{uuid.uuid4().hex[:8]}"
        )
        other_profile = ProfileFactory.create_wholesaler_profile(
            db,
            user_id=other_user.id,
            username=f"other_{uuid.uuid4().hex[:8]}",
            company_id=other_company.id
        )
        
        other_token = create_access_token({"sub": str(other_user.id)})
        
        response = client.get(
            f"/contracts/{contract_id}",
            headers=auth_headers(other_token, other_profile.id)
        )
        
        assert response.status_code == 403
        assert "permission to access this contract" in response.json()["detail"]

    def test_list_contracts_success(
        self, client: TestClient, db: Session,
        supplier_token_and_profile, supplier_company, receiver_company, centers
    ):
        """계약 목록 조회 성공 테스트"""
        token, profile = supplier_token_and_profile
        supplier_center = centers[0]
        receiver_center = centers[2]
        
        # 여러 계약 생성
        for i in range(3):
            contract_data = {
                "title": f"목록 테스트 계약 {i+1}",
                "supplier_company_id": str(supplier_company.id),
                "receiver_company_id": str(receiver_company.id),
                "departure_center_id": str(supplier_center.id),
                "arrival_center_id": str(receiver_center.id),
                "items": [
                    {
                        "contract_id": str(uuid.uuid4()),
                        "product_name": "쌀",
                        "quality": ProductQuality.A.value,
                        "quantity": 100,
                        "unit_price": 10000.0,
                        "total_price": 1000000.0
                    }
                ]
            }
            
            response = client.post(
                "/contracts/",
                json=contract_data,
                headers=auth_headers(token, profile.id)
            )
            assert response.status_code == 201
        
        # 계약 목록 조회
        response = client.get(
            "/contracts/",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) >= 3  # 최소 3개 이상의 계약이 있어야 함

    def test_list_contracts_with_filters(
        self, client: TestClient, db: Session,
        supplier_token_and_profile, supplier_company, receiver_company, centers
    ):
        """필터를 사용한 계약 목록 조회 테스트"""
        token, profile = supplier_token_and_profile
        supplier_center = centers[0]
        receiver_center = centers[2]
        
        # 계약 생성
        contract_data = {
            "title": "필터 테스트 계약",
            "supplier_company_id": str(supplier_company.id),
            "receiver_company_id": str(receiver_company.id),
            "departure_center_id": str(supplier_center.id),
            "arrival_center_id": str(receiver_center.id),
            "contract_status": ContractStatus.DRAFT.value,
            "items": [
                {
                    "contract_id": str(uuid.uuid4()),
                    "product_name": "쌀",
                    "quality": ProductQuality.A.value,
                    "quantity": 100,
                    "unit_price": 10000.0,
                    "total_price": 1000000.0
                }
            ]
        }
        
        create_response = client.post(
            "/contracts/",
            json=contract_data,
            headers=auth_headers(token, profile.id)
        )
        assert create_response.status_code == 201
        
        # 필터를 사용한 목록 조회
        response = client.get(
            "/contracts/",
            params={
                "contract_status": ContractStatus.DRAFT.value,
                "is_supplier": True,
                "limit": 10
            },
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) > 0

    def test_update_contract_success(
        self, client: TestClient, db: Session,
        supplier_token_and_profile, supplier_company, receiver_company, centers
    ):
        """계약 수정 성공 테스트"""
        token, profile = supplier_token_and_profile
        supplier_center = centers[0]
        receiver_center = centers[2]
        
        # 먼저 계약 생성
        contract_data = {
            "title": "수정 전 계약",
            "supplier_company_id": str(supplier_company.id),
            "receiver_company_id": str(receiver_company.id),
            "departure_center_id": str(supplier_center.id),
            "arrival_center_id": str(receiver_center.id),
            "items": [
                {
                    "contract_id": str(uuid.uuid4()),
                    "product_name": "쌀",
                    "quality": ProductQuality.A.value,
                    "quantity": 100,
                    "unit_price": 10000.0,
                    "total_price": 1000000.0
                }
            ]
        }
        
        create_response = client.post(
            "/contracts/",
            json=contract_data,
            headers=auth_headers(token, profile.id)
        )
        assert create_response.status_code == 201
        contract_id = create_response.json()["id"]
        
        # 계약 수정
        update_data = {
            "title": "수정된 계약",
            "notes": "수정된 계약입니다.",
            "contract_status": ContractStatus.APPROVED.value
        }
        
        response = client.put(
            f"/contracts/{contract_id}",
            json=update_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == "수정된 계약"
        assert result["notes"] == "수정된 계약입니다."
        assert result["contract_status"] == ContractStatus.APPROVED.value

    def test_delete_contract_success(
        self, client: TestClient, db: Session,
        supplier_token_and_profile, supplier_company, receiver_company, centers
    ):
        """계약 삭제 성공 테스트"""
        token, profile = supplier_token_and_profile
        supplier_center = centers[0]
        receiver_center = centers[2]
        
        # 먼저 계약 생성
        contract_data = {
            "title": "삭제할 계약",
            "supplier_company_id": str(supplier_company.id),
            "receiver_company_id": str(receiver_company.id),
            "departure_center_id": str(supplier_center.id),
            "arrival_center_id": str(receiver_center.id),
            "items": [
                {
                    "contract_id": str(uuid.uuid4()),
                    "product_name": "쌀",
                    "quality": ProductQuality.A.value,
                    "quantity": 100,
                    "unit_price": 10000.0,
                    "total_price": 1000000.0
                }
            ]
        }
        
        create_response = client.post(
            "/contracts/",
            json=contract_data,
            headers=auth_headers(token, profile.id)
        )
        assert create_response.status_code == 201
        contract_id = create_response.json()["id"]
        
        # 계약 삭제
        response = client.delete(
            f"/contracts/{contract_id}",
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 204
        
        # 삭제된 계약 조회 시도
        get_response = client.get(
            f"/contracts/{contract_id}",
            headers=auth_headers(token, profile.id)
        )
        
        assert get_response.status_code == 404

    def test_contract_unauthorized(
        self, client: TestClient, db: Session
    ):
        """인증되지 않은 사용자의 계약 접근 시 401 오류"""
        contract_id = str(uuid.uuid4())
        
        # 인증 없이 계약 조회
        response = client.get(f"/contracts/{contract_id}")
        assert response.status_code == 401
        
        # 인증 없이 계약 목록 조회
        response = client.get("/contracts/")
        assert response.status_code == 401
        
        # 인증 없이 계약 생성
        response = client.post("/contracts/", json={})
        assert response.status_code == 401

    def test_contract_invalid_data(
        self, client: TestClient, db: Session,
        supplier_token_and_profile, supplier_company, receiver_company, centers
    ):
        """잘못된 데이터로 계약 생성 시 422 오류"""
        token, profile = supplier_token_and_profile
        
        # 필수 필드가 없는 데이터
        invalid_data = {
            "notes": "잘못된 계약"
            # title과 items가 없음
        }
        
        response = client.post(
            "/contracts/",
            json=invalid_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 422  # Validation Error