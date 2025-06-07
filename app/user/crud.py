from sqlalchemy.orm import Session
from typing import Optional, Tuple
from uuid import UUID
from app.user.models import User
from app.core.auth.schemas import GoogleUserInfo, TokenPair
from app.core.auth.utils import create_access_token, create_refresh_token
from app.user.schemas import UserCreateOAuth, UserUpdate

def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """
    ID로 사용자를 조회합니다.
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    이메일로 사용자를 조회합니다.
    """
    return db.query(User).filter(User.email == email).first()

def get_user_by_oauth(db: Session, oauth_sub: str) -> Optional[User]:
    """
    Google OAuth sub로 사용자를 조회합니다.
    """
    return db.query(User).filter(
        User.oauth_provider == "google",
        User.oauth_sub == oauth_sub
    ).first()

def create_user(
    db: Session,
    user_info: GoogleUserInfo
) -> User:
    """
    새로운 사용자를 생성합니다.
    """
    db_user = User(
        email=user_info.email,
        name=user_info.name,
        oauth_provider="google",
        oauth_sub=user_info.sub,
        picture_url=user_info.picture
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_or_create_user(
    db: Session,
    user_info: GoogleUserInfo
) -> User:
    """
    사용자를 조회하거나 생성합니다.
    """
    # OAuth 정보로 사용자 조회
    user = get_user_by_oauth(db, user_info.sub)
    if user:
        # 기존 사용자 정보 업데이트
        user.name = user_info.name
        user.email = user_info.email
        if user_info.picture:
            user.picture_url = user_info.picture
        db.commit()
        db.refresh(user)
        return user
    
    # 이메일로 사용자 조회
    user = get_user_by_email(db, user_info.email)
    if user:
        # OAuth 정보 업데이트
        user.oauth_provider = "google"
        user.oauth_sub = user_info.sub
        user.name = user_info.name
        if user_info.picture:
            user.picture_url = user_info.picture
        db.commit()
        db.refresh(user)
        return user
    
    # 새 사용자 생성
    return create_user(db=db, user_info=user_info)

def get_or_create_oauth_user(
    db: Session,
    user_info: UserCreateOAuth
) -> Tuple[User, TokenPair]:
    """
    OAuth 회원가입/로그인용 유틸리티 함수 (테스트 및 API 호환)
    """
    google_user_info = GoogleUserInfo(
        email=user_info.email,
        name=user_info.name,
        sub=user_info.oauth_sub,
        picture=user_info.picture_url
    )
    user = get_or_create_user(db=db, user_info=google_user_info)
    
    # 실제 토큰 생성
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    token_pair = TokenPair(
        access_token=access_token,
        refresh_token=refresh_token
    )
    return user, token_pair

def update_user(db: Session, user_id: int, update_data: UserUpdate) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user 