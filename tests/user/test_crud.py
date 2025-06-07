import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from app.user.models import User
from app.user.crud import (
    get_user_by_id,
    get_user_by_email,
    get_user_by_oauth,
    create_user,
    get_or_create_user
)
from app.core.auth.schemas import GoogleUserInfo

def test_create_user(db: Session):
    """새로운 사용자 생성 테스트"""
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_123",
        picture="https://example.com/picture.jpg"
    )
    
    user = create_user(db, user_info)
    
    assert user.email == user_info.email
    assert user.name == user_info.name
    assert user.oauth_sub == user_info.sub
    assert user.picture_url == user_info.picture
    assert user.id is not None

def test_get_user_by_id(db: Session):
    """ID로 사용자 조회 테스트"""
    # 테스트용 사용자 생성
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_123"
    )
    created_user = create_user(db, user_info)
    
    # ID로 조회
    user = get_user_by_id(db, created_user.id)
    
    assert user is not None
    assert user.id == created_user.id
    assert user.email == created_user.email

def test_get_user_by_email(db: Session):
    """이메일로 사용자 조회 테스트"""
    # 테스트용 사용자 생성
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_123"
    )
    created_user = create_user(db, user_info)
    
    # 이메일로 조회
    user = get_user_by_email(db, created_user.email)
    
    assert user is not None
    assert user.email == created_user.email
    assert user.id == created_user.id

def test_get_user_by_oauth(db: Session):
    """OAuth sub로 사용자 조회 테스트"""
    # 테스트용 사용자 생성
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_123"
    )
    created_user = create_user(db, user_info)
    
    # OAuth sub로 조회
    user = get_user_by_oauth(db, created_user.oauth_sub)
    
    assert user is not None
    assert user.oauth_sub == created_user.oauth_sub
    assert user.id == created_user.id

def test_get_or_create_user_existing(db: Session):
    """기존 사용자 조회/생성 테스트"""
    # 테스트용 사용자 생성
    user_info = GoogleUserInfo(
        email="test@example.com",
        name="Test User",
        sub="google_123"
    )
    created_user = create_user(db, user_info)
    
    # 동일한 정보로 get_or_create_user 호출
    user = get_or_create_user(db, user_info)
    
    assert user is not None
    assert user.id == created_user.id
    assert user.email == created_user.email

def test_get_or_create_user_new(db: Session):
    """새로운 사용자 조회/생성 테스트"""
    user_info = GoogleUserInfo(
        email="new@example.com",
        name="New User",
        sub="google_456"
    )
    
    user = get_or_create_user(db, user_info)
    
    assert user is not None
    assert user.email == user_info.email
    assert user.name == user_info.name
    assert user.oauth_sub == user_info.sub 