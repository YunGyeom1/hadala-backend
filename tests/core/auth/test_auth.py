import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from jose import jwt
from datetime import datetime, timedelta
from app.core.auth import utils, crud, schemas
from app.core.config import settings
from tests.factories import UserFactory, ProfileFactory


class TestAuthUtils:
    """인증 유틸리티 함수 테스트"""
    
    def test_create_access_token(self):
        """액세스 토큰 생성 테스트"""
        data = {"sub": "test_user_id"}
        token = utils.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # 토큰 디코딩하여 검증
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "test_user_id"
        assert payload["token_type"] == "access"
    
    def test_create_refresh_token(self):
        """리프레시 토큰 생성 테스트"""
        data = {"sub": "test_user_id"}
        token = utils.create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # 토큰 디코딩하여 검증
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "test_user_id"
        assert payload["token_type"] == "refresh"
    
    def test_verify_access_token_valid(self):
        """유효한 액세스 토큰 검증 테스트"""
        data = {"sub": "test_user_id"}
        token = utils.create_access_token(data)
        
        payload = utils.verify_access_token(token)
        assert payload["sub"] == "test_user_id"
        assert payload["token_type"] == "access"
    
    def test_verify_access_token_invalid(self):
        """유효하지 않은 액세스 토큰 검증 테스트"""
        with pytest.raises(HTTPException) as exc_info:
            utils.verify_access_token("invalid_token")
        
        assert exc_info.value.status_code == 401
    
    def test_verify_refresh_token_valid(self):
        """유효한 리프레시 토큰 검증 테스트"""
        data = {"sub": "test_user_id"}
        token = utils.create_refresh_token(data)
        
        payload = utils.verify_refresh_token(token)
        assert payload["sub"] == "test_user_id"
        assert payload["token_type"] == "refresh"
    
    def test_verify_refresh_token_invalid(self):
        """유효하지 않은 리프레시 토큰 검증 테스트"""
        with pytest.raises(HTTPException) as exc_info:
            utils.verify_refresh_token("invalid_token")
        
        assert exc_info.value.status_code == 401
    
    def test_verify_token_type_mismatch(self):
        """토큰 타입 불일치 테스트"""
        # 액세스 토큰을 리프레시 토큰으로 검증하려고 시도
        data = {"sub": "test_user_id"}
        access_token = utils.create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            utils.verify_refresh_token(access_token)
        
        assert exc_info.value.status_code == 401
    
    @patch('app.core.auth.utils.id_token.verify_oauth2_token')
    def test_verify_google_id_token_valid(self, mock_verify):
        """유효한 Google ID 토큰 검증 테스트"""
        mock_verify.return_value = {
            "sub": "google_user_id",
            "email": "test@example.com",
            "email_verified": True,
            "aud": settings.GOOGLE_CLIENT_ID
        }
        
        result = utils.verify_google_id_token("valid_id_token")
        
        assert result is not None
        assert result["sub"] == "google_user_id"
        assert result["email"] == "test@example.com"
        assert result["email_verified"] is True
    
    @patch('app.core.auth.utils.id_token.verify_oauth2_token')
    def test_verify_google_id_token_invalid(self, mock_verify):
        """유효하지 않은 Google ID 토큰 검증 테스트"""
        mock_verify.side_effect = Exception("Invalid token")
        
        result = utils.verify_google_id_token("invalid_id_token")
        
        assert result is None
    
    @patch('app.core.auth.utils.id_token.verify_oauth2_token')
    def test_verify_google_id_token_aud_mismatch(self, mock_verify):
        """Google ID 토큰 aud 불일치 테스트"""
        mock_verify.return_value = {
            "sub": "google_user_id",
            "email": "test@example.com",
            "email_verified": True,
            "aud": "wrong_client_id"
        }
        
        result = utils.verify_google_id_token("valid_id_token")
        
        assert result is None


class TestAuthCRUD:
    """인증 CRUD 함수 테스트"""
    
    def test_get_user_by_oauth_existing(self, db):
        """기존 OAuth 사용자 조회 테스트"""
        user = UserFactory.create_user(db, oauth_provider="google", oauth_sub="test_sub")
        
        result = crud.get_user_by_oauth(db, provider="google", sub="test_sub")
        
        assert result is not None
        assert result.id == user.id
        assert result.oauth_provider == "google"
        assert result.oauth_sub == "test_sub"
    
    def test_get_user_by_oauth_not_found(self, db):
        """존재하지 않는 OAuth 사용자 조회 테스트"""
        result = crud.get_user_by_oauth(db, provider="google", sub="non_existent_sub")
        
        assert result is None
    
    def test_create_user_by_google_oauth(self, db):
        """Google OAuth 사용자 생성 테스트"""
        user_info = {
            "sub": "google_user_id",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/picture.jpg"
        }
        
        user = crud.create_user_by_google_oauth(db, user_info)
        
        assert user is not None
        assert user.oauth_provider == "google"
        assert user.oauth_sub == "google_user_id"
        assert user.picture_url == "https://example.com/picture.jpg"


class TestAuthAPI:
    """인증 API 엔드포인트 테스트"""
    
    @patch('app.core.auth.utils.verify_google_id_token')
    def test_google_login_success(self, mock_verify, client, db):
        """Google 로그인 성공 테스트"""
        mock_verify.return_value = {
            "sub": "google_user_id",
            "email": "test@example.com",
            "email_verified": True,
            "aud": settings.GOOGLE_CLIENT_ID
        }
        
        response = client.post("/auth/google-login", json={"id_token": "valid_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @patch('app.core.auth.utils.verify_google_id_token')
    def test_google_login_invalid_token(self, mock_verify, client):
        """유효하지 않은 토큰으로 Google 로그인 테스트"""
        mock_verify.return_value = None
        
        response = client.post("/auth/google-login", json={"id_token": "invalid_token"})
        
        assert response.status_code == 400
        assert "유효하지 않은 ID 토큰입니다" in response.json()["detail"]
    
    @patch('app.core.auth.utils.verify_google_id_token')
    def test_google_login_unverified_email(self, mock_verify, client):
        """인증되지 않은 이메일로 Google 로그인 테스트"""
        mock_verify.return_value = {
            "sub": "google_user_id",
            "email": "test@example.com",
            "email_verified": False,
            "aud": settings.GOOGLE_CLIENT_ID
        }
        
        response = client.post("/auth/google-login", json={"id_token": "valid_token"})
        
        assert response.status_code == 400
        assert "이메일 인증되지 않은 계정입니다" in response.json()["detail"]
    
    def test_verify_refresh_token_valid(self, client):
        """유효한 리프레시 토큰 검증 테스트"""
        # 유효한 리프레시 토큰 생성
        data = {"sub": "test_user_id"}
        refresh_token = utils.create_refresh_token(data)
        
        response = client.post("/auth/verify", json={"refresh_token": refresh_token})
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["error"] is None
    
    def test_verify_refresh_token_invalid(self, client):
        """유효하지 않은 리프레시 토큰 검증 테스트"""
        response = client.post("/auth/verify", json={"refresh_token": "invalid_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error"] is not None
    
    def test_refresh_token_success(self, client):
        """토큰 갱신 성공 테스트"""
        # 유효한 리프레시 토큰 생성
        data = {"sub": "test_user_id"}
        refresh_token = utils.create_refresh_token(data)
        
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client):
        """유효하지 않은 리프레시 토큰으로 갱신 테스트"""
        response = client.post("/auth/refresh", json={"refresh_token": "invalid_token"})
        
        assert response.status_code == 401
        assert "Refresh token 오류" in response.json()["detail"]

