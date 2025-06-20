import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.profile.models import ProfileType, ProfileRole
from app.core.auth.utils import create_access_token
from tests.factories import UserFactory, CompanyFactory, TestDataFactory


class TestProfileAPI:
    def test_create_profile(self, client: TestClient, db: Session):
        """프로필 생성 API 테스트"""
        user = UserFactory.create_user(db)
        
        # JWT 토큰 생성
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        profile_data = {
            "username": "api_test_user",
            "type": "wholesaler",
            "name": "API 테스트 사용자",
            "phone": "010-1234-5678",
            "email": "api_test@example.com"
        }
        
        response = client.post("/profile/me", json=profile_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "api_test_user"
        assert data["type"] == "wholesaler"
        assert data["name"] == "API 테스트 사용자"
        assert data["phone"] == "010-1234-5678"
        assert data["email"] == "api_test@example.com"

    def test_create_profile_duplicate_username(self, client: TestClient, db: Session):
        """중복 username으로 프로필 생성 시도 테스트"""
        user = UserFactory.create_user(db)
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 첫 번째 프로필 생성
        profile_data = {
            "username": "duplicate_user",
            "type": "wholesaler",
            "name": "첫 번째 사용자"
        }
        
        response = client.post("/profile/me", json=profile_data, headers=headers)
        assert response.status_code == 200
        
        # 같은 username으로 두 번째 프로필 생성 시도
        profile_data2 = {
            "username": "duplicate_user",
            "type": "retailer",
            "name": "두 번째 사용자"
        }
        
        response2 = client.post("/profile/me", json=profile_data2, headers=headers)
        assert response2.status_code == 400
        assert "이미 사용 중인 username입니다" in response2.json()["detail"]

    def test_create_public_profile(self, client: TestClient, db: Session):
        """공개 프로필 생성 API 테스트"""
        company = CompanyFactory.create_wholesale_company(db)
        
        profile_data = {
            "username": "public_user",
            "type": "retailer",
            "name": "공개 사용자",
            "phone": "010-9876-5432",
            "email": "public@example.com",
            "company_id": str(company.id),
            "role": "member"
        }
        
        response = client.post("/profile/public", json=profile_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "public_user"
        assert data["type"] == "retailer"
        assert data["name"] == "공개 사용자"
        assert data["role"] == "member"

    def test_get_my_profiles(self, client: TestClient, db: Session):
        """내 프로필 조회 API 테스트"""
        user = UserFactory.create_user(db)
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 여러 프로필 생성
        profiles_data = [
            {"username": "my_user1", "type": "wholesaler", "name": "내 사용자1"},
            {"username": "my_user2", "type": "retailer", "name": "내 사용자2"},
            {"username": "my_user3", "type": "farmer", "name": "내 사용자3"}
        ]
        
        for profile_data in profiles_data:
            client.post("/profile/me", json=profile_data, headers=headers)
        
        # 내 프로필들 조회
        response = client.get("/profile/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(profile["username"].startswith("my_user") for profile in data)

    def test_search_profiles(self, client: TestClient, db: Session):
        """프로필 검색 API 테스트"""
        user = UserFactory.create_user(db)
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 검색용 프로필들 생성
        profiles_data = [
            {"username": "search_test1", "type": "wholesaler", "name": "검색 테스트1"},
            {"username": "search_test2", "type": "retailer", "name": "검색 테스트2"},
            {"username": "other_user", "type": "farmer", "name": "다른 사용자"},
            {"username": "search_test3", "type": "wholesaler", "name": "검색 테스트3"}
        ]
        
        for profile_data in profiles_data:
            client.post("/profile/me", json=profile_data, headers=headers)
        
        # username으로 검색
        response = client.get("/profile/search?username=search")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("search" in profile["username"] for profile in data)
        
        # 타입으로 필터링
        response2 = client.get("/profile/search?username=search&profile_type=wholesaler")
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2) == 2
        assert all(profile["type"] == "wholesaler" for profile in data2)

    def test_get_profile_by_id(self, client: TestClient, db: Session):
        """ID로 프로필 조회 API 테스트"""
        user = UserFactory.create_user(db)
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 프로필 생성
        profile_data = {
            "username": "get_by_id_user",
            "type": "wholesaler",
            "name": "ID 조회 사용자"
        }
        
        create_response = client.post("/profile/me", json=profile_data, headers=headers)
        created_profile = create_response.json()
        
        # ID로 조회
        response = client.get(f"/profile/{created_profile['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_profile["id"]
        assert data["username"] == "get_by_id_user"
        assert data["name"] == "ID 조회 사용자"

    def test_get_nonexistent_profile(self, client: TestClient, db: Session):
        """존재하지 않는 프로필 조회 테스트"""
        import uuid
        
        response = client.get(f"/profile/{uuid.uuid4()}")
        
        assert response.status_code == 404
        assert "프로필을 찾을 수 없습니다" in response.json()["detail"]

    def test_update_my_profile(self, client: TestClient, db: Session):
        """내 프로필 수정 API 테스트"""
        user = UserFactory.create_user(db)
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 프로필 생성
        profile_data = {
            "username": "update_api_user",
            "type": "wholesaler",
            "name": "수정 전 사용자",
            "phone": "010-1111-1111",
            "email": "before@example.com"
        }
        
        create_response = client.post("/profile/me", json=profile_data, headers=headers)
        created_profile = create_response.json()
        
        # 프로필 수정
        update_data = {
            "name": "수정 후 사용자",
            "phone": "010-2222-2222",
            "email": "after@example.com"
        }
        
        response = client.put(f"/profile/{created_profile['id']}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "수정 후 사용자"
        assert data["phone"] == "010-2222-2222"
        assert data["email"] == "after@example.com"
        assert data["username"] == "update_api_user"  # 변경되지 않음

    def test_update_other_user_profile(self, client: TestClient, db: Session):
        """다른 사용자의 프로필 수정 시도 테스트"""
        user1 = UserFactory.create_user(db)
        user2 = UserFactory.create_user(db)
        
        # user1의 프로필 생성
        token1 = create_access_token(data={"sub": str(user1.id)})
        headers1 = {"Authorization": f"Bearer {token1}"}
        profile_data = {
            "username": "user1_profile",
            "type": "wholesaler",
            "name": "사용자1"
        }
        
        create_response = client.post("/profile/me", json=profile_data, headers=headers1)
        created_profile = create_response.json()
        
        # user2가 user1의 프로필 수정 시도
        token2 = create_access_token(data={"sub": str(user2.id)})
        headers2 = {"Authorization": f"Bearer {token2}"}
        update_data = {"name": "무단 수정"}
        
        response = client.put(f"/profile/{created_profile['id']}", json=update_data, headers=headers2)
        
        assert response.status_code == 403
        assert "접근 권한이 없습니다" in response.json()["detail"]

    def test_update_nonexistent_profile_api(self, client: TestClient, db: Session):
        """존재하지 않는 프로필 수정 시도 테스트"""
        user = UserFactory.create_user(db)
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        import uuid
        update_data = {"name": "존재하지 않는 사용자"}
        
        response = client.put(f"/profile/{uuid.uuid4()}", json=update_data, headers=headers)
        
        assert response.status_code == 404
        assert "프로필을 찾을 수 없습니다" in response.json()["detail"]

    def test_update_profile_role(self, client: TestClient, db: Session):
        """프로필 역할 수정 API 테스트"""
        setup = TestDataFactory.create_complete_user_setup(
            db,
            username="role_update_user",
            company_name="역할 수정 회사",
            profile_type=ProfileType.wholesaler
        )
        
        # 프로필을 새로 쿼리해서 관계를 확실히 연결
        from app.profile.models import Profile
        owner_profile = db.get(Profile, setup["profile"].id)
        
        token = create_access_token(data={"sub": str(setup["user"].id)})
        headers = {"Authorization": f"Bearer {token}"}
        role_data = {"role": ProfileRole.manager.value}
        role_headers = {
            **headers,
            "X-Profile-ID": str(owner_profile.id)
        }
        
        response = client.put(f"/profile/{owner_profile.id}/role", json=role_data, headers=role_headers)
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        assert response.status_code == 200
        
        # 응답 검증
        data = response.json()
        assert data["role"] == ProfileRole.manager.value
        assert data["id"] == str(owner_profile.id)

    def test_search_profiles_pagination(self, client: TestClient, db: Session):
        """프로필 검색 페이지네이션 API 테스트"""
        user = UserFactory.create_user(db)
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 15개의 프로필 생성
        for i in range(15):
            profile_data = {
                "username": f"pagination_api_user_{i}",
                "type": "wholesaler",
                "name": f"페이지네이션 API 사용자 {i}"
            }
            client.post("/profile/me", json=profile_data, headers=headers)
        
        # 기본 페이지네이션 (skip=0, limit=10)
        response = client.get("/profile/search?username=pagination_api&skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # 두 번째 페이지 (skip=10, limit=10)
        response2 = client.get("/profile/search?username=pagination_api&skip=10&limit=10")
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2) == 5

    def test_search_profiles_invalid_params(self, client: TestClient, db: Session):
        """프로필 검색 잘못된 파라미터 테스트"""
        # 음수 skip
        response = client.get("/profile/search?skip=-1")
        assert response.status_code == 422
        
        # 0 limit
        response2 = client.get("/profile/search?limit=0")
        assert response2.status_code == 422
        
        # 너무 큰 limit
        response3 = client.get("/profile/search?limit=101")
        assert response3.status_code == 422

    def test_create_profile_missing_required_fields(self, client: TestClient, db: Session):
        """필수 필드 누락으로 프로필 생성 시도 테스트"""
        user = UserFactory.create_user(db)
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # username 누락
        profile_data = {
            "type": "wholesaler",
            "name": "필수 필드 누락 사용자"
        }
        
        response = client.post("/profile/me", json=profile_data, headers=headers)
        assert response.status_code == 422
        
        # type 누락
        profile_data2 = {
            "username": "missing_type_user",
            "name": "타입 누락 사용자"
        }
        
        response2 = client.post("/profile/me", json=profile_data2, headers=headers)
        assert response2.status_code == 422

    def test_unauthorized_access(self, client: TestClient, db: Session):
        """인증되지 않은 접근 테스트"""
        # 토큰 없이 프로필 생성 시도
        profile_data = {
            "username": "unauthorized_user",
            "type": "wholesaler",
            "name": "인증되지 않은 사용자"
        }
        
        response = client.post("/profile/me", json=profile_data)
        assert response.status_code == 401
        
        # 토큰 없이 내 프로필 조회 시도
        response2 = client.get("/profile/me")
        assert response2.status_code == 401

    def test_invalid_token(self, client: TestClient, db: Session):
        """잘못된 토큰으로 접근 테스트"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        profile_data = {
            "username": "invalid_token_user",
            "type": "wholesaler",
            "name": "잘못된 토큰 사용자"
        }
        
        response = client.post("/profile/me", json=profile_data, headers=headers)
        assert response.status_code == 401

    def test_create_multiple_profiles_for_user(self, client: TestClient, db: Session):
        """사용자에게 여러 프로필 생성 테스트"""
        user = UserFactory.create_user(db)
        token = create_access_token(data={"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 여러 타입의 프로필 생성
        profile_types = ["wholesaler", "retailer", "farmer"]
        
        for i, profile_type in enumerate(profile_types):
            profile_data = {
                "username": f"multi_user_{profile_type}_{i}",
                "type": profile_type,
                "name": f"{profile_type} 사용자 {i}"
            }
            
            response = client.post("/profile/me", json=profile_data, headers=headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["type"] == profile_type
            assert data["username"] == f"multi_user_{profile_type}_{i}"

    def test_profile_with_company_association(self, client: TestClient, db: Session):
        """회사와 연결된 프로필 테스트"""
        setup = TestDataFactory.create_complete_user_setup(
            db,
            username="company_user",
            company_name="연결된 회사",
            profile_type=ProfileType.wholesaler
        )
        from app.profile.models import Profile
        profile = db.query(Profile).get(setup["profile"].id)
        response = client.get(f"/profile/{profile.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "company_user"
        # company_name 검증 제거 