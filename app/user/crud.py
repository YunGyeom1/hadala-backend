from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.user.models import User

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

def get_user_by_oauth(db: Session, provider: str, oauth_sub: str) -> Optional[User]:
    """
    OAuth 제공자와 sub로 사용자를 조회합니다.
    """
    return db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_sub == oauth_sub
    ).first()

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

def get_or_create_user(
    db: Session,
    email: str,
    name: str,
    oauth_provider: str,
    oauth_sub: str,
    picture_url: Optional[str] = None
) -> User:
    """
    사용자를 조회하거나 생성합니다.
    """
    # OAuth 정보로 사용자 조회
    user = get_user_by_oauth(db, oauth_provider, oauth_sub)
    if user:
        return user
    
    # 이메일로 사용자 조회
    user = get_user_by_email(db, email)
    if user:
        # OAuth 정보 업데이트
        user.oauth_provider = oauth_provider
        user.oauth_sub = oauth_sub
        if picture_url:
            user.picture_url = picture_url
        db.commit()
        db.refresh(user)
        return user
    
    # 새 사용자 생성
    return create_user(
        db=db,
        email=email,
        name=name,
        oauth_provider=oauth_provider,
        oauth_sub=oauth_sub,
        picture_url=picture_url
    )

def get_or_create_oauth_user(
    db: Session,
    user_info
):
    """
    OAuth 회원가입/로그인용 유틸리티 함수 (테스트 및 API 호환)
    """
    return get_or_create_user(
        db=db,
        email=user_info.email,
        name=user_info.name,
        oauth_provider=user_info.oauth_provider,
        oauth_sub=user_info.oauth_sub,
        picture_url=getattr(user_info, "picture_url", None)
    ), None  # 토큰 페어는 실제 서비스에서 반환 