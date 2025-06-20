import pytest
from datetime import time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from tests.factories import (
    UserFactory, ProfileFactory, CompanyFactory, CenterFactory
)
from app.core.auth.utils import create_access_token
from app.profile.models import ProfileType, ProfileRole
import uuid

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
    
    # 프로필의 company_id를 설정
    profile.company_id = company.id
    db.commit()
    db.refresh(profile)
    
    return company

@pytest.fixture
def centers(db: Session, wholesale_company):
    """테스트용 센터들을 생성합니다."""
    centers = CenterFactory.create_multiple_centers(
        db, company_id=wholesale_company.id, count=3
    )
    return centers

@pytest.fixture
def manager_profile(db: Session, wholesale_company):
    """센터 매니저 프로필을 생성합니다."""
    user = UserFactory.create_user(db)
    profile = ProfileFactory.create_wholesaler_profile(
        db, 
        user_id=user.id, 
        username=f"manager_{uuid.uuid4().hex[:8]}",
        company_id=wholesale_company.id,
        role=ProfileRole.manager
    )
    return profile

def auth_headers(token, profile_id):
    """인증 헤더를 생성합니다."""
    return {"Authorization": f"Bearer {token}", "X-Profile-ID": str(profile_id)}

class TestCenterAPI:
    """센터 API 테스트"""
    
    def test_update_center_success(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers
    ):
        """센터 정보 수정 성공 테스트"""
        token, profile = owner_token_and_profile
        center = centers[0]
        
        update_data = {
            "name": "수정된 센터명",
            "address": "서울시 강남구 테헤란로 123",
            "region": "강남",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "phone": "02-1234-5678",
            "operating_start": "09:00:00",
            "operating_end": "18:00:00",
            "is_operational": True
        }
        
        response = client.put(
            f"/centers/{center.id}",
            json=update_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "수정된 센터명"
        assert result["address"] == "서울시 강남구 테헤란로 123"
        assert result["region"] == "강남"
        assert result["latitude"] == 37.5665
        assert result["longitude"] == 126.9780
        assert result["phone"] == "02-1234-5678"
        assert result["operating_start"] == "09:00:00"
        assert result["operating_end"] == "18:00:00"
        assert result["is_operational"] == True

    def test_update_center_with_manager(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers, manager_profile
    ):
        """매니저를 지정하여 센터 정보 수정 테스트"""
        token, profile = owner_token_and_profile
        center = centers[0]
        
        update_data = {
            "name": "매니저 지정 센터",
            "manager_profile_id": str(manager_profile.id)
        }
        
        response = client.put(
            f"/centers/{center.id}",
            json=update_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "매니저 지정 센터"
        assert result["manager_profile_id"] == str(manager_profile.id)

    def test_update_center_not_found(
        self, client: TestClient, db: Session,
        owner_token_and_profile
    ):
        """존재하지 않는 센터 수정 시 404 오류"""
        token, profile = owner_token_and_profile
        non_existent_center_id = str(uuid.uuid4())
        
        update_data = {"name": "존재하지 않는 센터"}
        
        response = client.put(
            f"/centers/{non_existent_center_id}",
            json=update_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 404
        assert "센터를 찾을 수 없습니다" in response.json()["detail"]

    def test_update_center_no_permission(
        self, client: TestClient, db: Session,
        wholesale_company, centers
    ):
        """권한이 없는 사용자의 센터 수정 시 403 오류"""
        # 다른 회사의 사용자 생성
        other_user = UserFactory.create_user(db)
        other_profile = ProfileFactory.create_wholesaler_profile(
            db,
            user_id=other_user.id,
            username=f"other_{uuid.uuid4().hex[:8]}"
        )
        other_company = CompanyFactory.create_wholesale_company(
            db, owner_id=other_profile.id, name=f"다른 회사_{uuid.uuid4().hex[:8]}"
        )
        
        token = create_access_token({"sub": str(other_user.id)})
        center = centers[0]
        
        update_data = {"name": "무단 수정"}
        
        response = client.put(
            f"/centers/{center.id}",
            json=update_data,
            headers=auth_headers(token, other_profile.id)
        )
        
        assert response.status_code == 403
        assert "수정 권한이 없습니다" in response.json()["detail"]

    def test_update_center_unauthorized(
        self, client: TestClient, db: Session, centers
    ):
        """인증되지 않은 사용자의 센터 수정 시 401 오류"""
        center = centers[0]
        update_data = {"name": "무단 수정"}
        
        response = client.put(
            f"/centers/{center.id}",
            json=update_data
        )
        
        assert response.status_code == 401

    def test_update_center_invalid_manager(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers
    ):
        """존재하지 않는 매니저 프로필로 센터 수정 시 400 오류"""
        token, profile = owner_token_and_profile
        center = centers[0]
        non_existent_profile_id = str(uuid.uuid4())
        
        update_data = {
            "name": "잘못된 매니저",
            "manager_profile_id": non_existent_profile_id
        }
        
        response = client.put(
            f"/centers/{center.id}",
            json=update_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 400
        assert "업데이트에 실패했습니다" in response.json()["detail"]

    def test_update_center_partial_data(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers
    ):
        """부분 데이터로 센터 수정 테스트"""
        token, profile = owner_token_and_profile
        center = centers[0]
        
        # 기존 센터 정보 확인
        original_name = center.name
        
        update_data = {
            "phone": "02-9876-5432",
            "is_operational": False
        }
        
        response = client.put(
            f"/centers/{center.id}",
            json=update_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == original_name  # 이름은 변경되지 않음
        assert result["phone"] == "02-9876-5432"
        assert result["is_operational"] == False

    def test_update_center_by_manager(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers, manager_profile
    ):
        """센터 매니저가 자신의 센터를 수정하는 테스트"""
        token, profile = owner_token_and_profile
        center = centers[0]
        
        # 매니저 프로필의 company_id를 설정
        manager_profile.company_id = wholesale_company.id
        db.commit()
        db.refresh(manager_profile)
        
        # 먼저 매니저를 지정
        update_data = {"manager_profile_id": str(manager_profile.id)}
        response = client.put(
            f"/centers/{center.id}",
            json=update_data,
            headers=auth_headers(token, profile.id)
        )
        assert response.status_code == 200
        
        # 센터를 다시 조회하여 manager_profile_id가 설정되었는지 확인
        db.refresh(center)
        assert center.manager_profile_id == manager_profile.id
        
        # 매니저로 로그인하여 센터 수정 (매니저 프로필의 user_id를 사용)
        manager_token = create_access_token({"sub": str(manager_profile.user_id)})
        
        manager_update_data = {"name": "매니저가 수정한 센터"}
        response = client.put(
            f"/centers/{center.id}",
            json=manager_update_data,
            headers=auth_headers(manager_token, manager_profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "매니저가 수정한 센터"

    def test_update_center_invalid_time_format(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers
    ):
        """잘못된 시간 형식으로 센터 수정 시 422 오류"""
        token, profile = owner_token_and_profile
        center = centers[0]
        
        update_data = {
            "operating_start": "25:00:00",  # 잘못된 시간
            "operating_end": "invalid_time"
        }
        
        response = client.put(
            f"/centers/{center.id}",
            json=update_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 422  # Validation Error

    def test_update_center_empty_data(
        self, client: TestClient, db: Session,
        owner_token_and_profile, wholesale_company, centers
    ):
        """빈 데이터로 센터 수정 시 기존 데이터 유지"""
        token, profile = owner_token_and_profile
        center = centers[0]
        
        # 기존 센터 정보 저장
        original_name = center.name
        original_address = center.address
        
        update_data = {}
        
        response = client.put(
            f"/centers/{center.id}",
            json=update_data,
            headers=auth_headers(token, profile.id)
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == original_name
        assert result["address"] == original_address 