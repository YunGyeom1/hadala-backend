from sqlalchemy.orm import Session
from app.core.auth.models import User


def get_user_by_oauth(db: Session, provider: str, sub: str) -> User | None:
    return db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_sub == sub
    ).first()

def create_user_by_google_oauth(db: Session, user_info: dict) -> User:
    new_user = User(
        name=user_info.get("name", ""),
        email=user_info.get("email", ""),
        picture_url=user_info.get("picture", ""),
        oauth_provider="google",
        oauth_sub=user_info.get("sub")  # Google의 고유 user ID
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user