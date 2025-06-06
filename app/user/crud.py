from sqlalchemy.orm import Session
from typing import Optional, Tuple
from uuid import UUID
from fastapi import HTTPException

from app.user.models import User
from app.user.schemas import UserCreateOAuth
from app.core.security import create_token_pair

def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """
    ID로 사용자를 조회합니다.
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    이메일로 사용자를 조회합니다.
    """
    return db.query(User).filter(User.email == email).first()

def get_user_by_oauth(db: Session, provider: str, sub: str) -> Optional[User]:
    """
    OAuth 제공자와 sub로 사용자를 조회합니다.
    """
    return db.query(User).filter_by(oauth_provider=provider, oauth_sub=sub).first()

def create_user(
    db: Session,
    email: str,
    name: str,
    oauth_provider: str,
    oauth_sub: str,
    picture_url: Optional[str] = None
) -> User:
    """
    새로운 사용자를 생성합니다.
    """
    db_user = User(
        email=email,
        name=name,
        oauth_provider=oauth_provider,
        oauth_sub=oauth_sub,
        picture_url=picture_url
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_user_oauth(db: Session, user_data: UserCreateOAuth) -> User:
    """
    새로운 OAuth 사용자를 생성합니다.
    """
    # 이메일 중복 체크
    existing_user = db.query(User).filter_by(email=user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="이미 등록된 이메일입니다."
        )
    
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        oauth_provider=user_data.oauth_provider,
        oauth_sub=user_data.oauth_sub,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_or_create_oauth_user(db: Session, user_data: UserCreateOAuth) -> Tuple[User, str]:
    """
    사용자를 조회하거나 생성합니다.
    """
    user = get_user_by_oauth(db, user_data.oauth_provider, user_data.oauth_sub)
    if not user:
        user = create_user_oauth(db, user_data)
    
    # Access Token과 Refresh Token 생성
    token_pair = create_token_pair(data={"sub": str(user.id)})
    return user, token_pair