import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from app.user.crud import create_user
from app.core.auth.schemas import GoogleUserInfo
from app.core.auth.utils import create_token_pair, create_access_token, create_refresh_token
from app.main import app
from app.user.models import User

client = TestClient(app)

def test_login(client: TestClient, db):
    """로그인 테스트"""
    # 테스트 사용자 생성
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "company_id": str(uuid4()),
        "is_active": True,
        "is_superuser": False
    }
    user_info = GoogleUserInfo(
        email=user_data["email"],
        name="Test User",
        sub="test_login_sub",
        picture="https://example.com/picture.jpg"
    )
    create_user(db, user_info)
    
    # 로그인 요청
    response = client.post(
        "/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, db):
    """잘못된 비밀번호로 로그인 테스트"""
    # 테스트 사용자 생성
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "company_id": str(uuid4()),
        "is_active": True,
        "is_superuser": False
    }
    user_info = GoogleUserInfo(
        email=user_data["email"],
        name="Test User",
        sub="test_wrong_pw_sub",
        picture="https://example.com/picture.jpg"
    )
    create_user(db, user_info)
    
    # 잘못된 비밀번호로 로그인 요청
    response = client.post(
        "/auth/login",
        data={
            "username": user_data["email"],
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_login_nonexistent_user(client: TestClient):
    """존재하지 않는 사용자로 로그인 테스트"""
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "testpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_google_oauth_login(client: TestClient, db):
    """구글 OAuth 로그인 테스트"""
    # 테스트 사용자 생성
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_oauth_sub_123",
        picture="https://example.com/picture.jpg"
    )
    user = create_user(db, user_info)
    
    # 구글 OAuth 로그인 요청
    response = client.post(
        "/auth/google/login",
        json={
            "credential": "mock_google_credential"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_google_oauth_login_invalid_credential(client: TestClient):
    """잘못된 구글 인증 정보로 로그인 테스트"""
    response = client.post(
        "/auth/google/login",
        json={
            "credential": "invalid_credential"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google credential"

def test_refresh_token(client: TestClient, db):
    """토큰 갱신 테스트"""
    # 테스트 사용자 생성
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_oauth_sub_123",
        picture="https://example.com/picture.jpg"
    )
    user = create_user(db, user_info)
    
    # 토큰 생성
    access_token, refresh_token = create_token_pair({"sub": user_info.sub})
    
    # 토큰 갱신 요청
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_refresh_token_invalid(client: TestClient):
    """잘못된 리프레시 토큰으로 갱신 테스트"""
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "invalid_refresh_token"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"

def test_get_my_info(db, test_user):
    """내 정보 조회 테스트"""
    # 테스트용 사용자 생성
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_123"
    )
    user = create_user(db, user_info)
    
    # Access Token 생성
    access_token = create_access_token(data={"sub": str(user.id), "token_type": "access"})
    
    # API 호출
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["name"] == user.name

def test_update_my_info(db, test_user):
    """내 정보 수정 테스트"""
    # 테스트용 사용자 생성
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_123"
    )
    user = create_user(db, user_info)
    
    # Access Token 생성
    access_token = create_access_token(data={"sub": str(user.id), "token_type": "access"})
    
    # 업데이트할 정보
    update_data = {
        "name": "Updated Name",
        "picture_url": "https://example.com/new-picture.jpg"
    }
    
    # API 호출
    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["picture_url"] == update_data["picture_url"]

def test_oauth_login_new_user(db):
    """새로운 사용자 OAuth 로그인 테스트"""
    login_data = {
        "email": "new@example.com",
        "name": "New User",
        "oauth_provider": "google",
        "oauth_sub": "google_456",
        "picture_url": "https://example.com/picture.jpg"
    }
    
    response = client.post("/users/oauth-login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == login_data["email"]
    assert data["user"]["name"] == login_data["name"]

def test_oauth_login_existing_user(db):
    """기존 사용자 OAuth 로그인 테스트"""
    # 테스트용 사용자 생성
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_123"
    )
    user = create_user(db, user_info)
    
    login_data = {
        "email": user.email,
        "name": user.name,
        "oauth_provider": "google",
        "oauth_sub": user.oauth_sub,
        "picture_url": user.picture_url
    }
    
    response = client.post("/users/oauth-login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == user.email
    assert data["user"]["name"] == user.name

def test_refresh_token(db, test_user):
    """토큰 갱신 테스트"""
    # 테스트용 사용자 생성
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_123"
    )
    user = create_user(db, user_info)
    
    # Refresh Token 생성
    refresh_token = create_refresh_token(data={"sub": str(user.id), "token_type": "refresh"})
    
    # API 호출
    response = client.post(
        "/users/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer" 