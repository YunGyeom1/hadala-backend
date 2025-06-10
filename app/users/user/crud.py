from sqlalchemy.orm import Session
from typing import Optional, Tuple
from uuid import UUID
from app.users.user.models import User
from app.core.auth.schemas import GoogleUserInfo
from app.users.user.schemas import UserUpdate

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


def update_user(db: Session, user_id: int, update_data: UserUpdate) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user 