import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.user.models import User
from app.user.crud import create_user

def test_google_oauth_signup(client: TestClient, db: Session):
    """Google OAuth 회원가입 테스트"""
    # 테스트용 Google OAuth 데이터
    test_data = {
        "email": "test@example.com",
        "name": "Test User",
        "oauth_provider": "google",
        "oauth_sub": "123456789",
        "picture_url": "https://example.com/picture.jpg"
    }
    
    # 테스트용 사용자 생성
    user = create_user(
        db=db,
        email=test_data["email"],
        name=test_data["name"],
        oauth_provider=test_data["oauth_provider"],
        oauth_sub=test_data["oauth_sub"],
        picture_url=test_data["picture_url"]
    )
    
    # 생성된 사용자 검증
    assert user.email == test_data["email"]
    assert user.name == test_data["name"]
    assert user.oauth_provider == test_data["oauth_provider"]
    assert user.oauth_sub == test_data["oauth_sub"]
    assert user.picture_url == test_data["picture_url"]

def test_google_oauth_login(client: TestClient, db: Session):
    """Google OAuth 로그인 테스트"""
    # 테스트용 사용자 생성
    test_user = create_user(
        db=db,
        email="login@example.com",
        name="Login User",
        oauth_provider="google",
        oauth_sub="987654321",
        picture_url="https://example.com/login_picture.jpg"
    )
    # test_user_id = str(test_user.id)  # DetachedInstanceError 방지
    
    # 로그인 요청
    response = client.post(
        "/auth/google-login",
        json={"id_token": "fake-id-token"}
    )
    
    # 응답 검증
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"]

def test_google_oauth_signup_and_login(client: TestClient):
    """Google OAuth 회원가입 및 로그인 통합 테스트 (mocked)"""
    fake_id_token = "fake-id-token"
    response = client.post(
        "/auth/google-login",
        json={"id_token": fake_id_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user_id"]

    # 토큰 검증
    verify_response = client.post(
        "/auth/verify",
        json={"access_token": data["access_token"]}
    )
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["valid"] is True
    assert verify_data["user_id"] == data["user_id"]

    # 리프레시 토큰으로 access_token 재발급
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": data["refresh_token"]}
    )
    assert refresh_response.status_code == 200 