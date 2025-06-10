from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID
from app.database.session import get_db
from app.core.auth.models import User
from app.core.auth.utils import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        token_data = verify_access_token(token)
        user_id = UUID(token_data["sub"])
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="인증된 사용자를 찾을 수 없습니다")
        return user
    except Exception:
        raise HTTPException(
            status_code=401, detail="인증 정보가 유효하지 않습니다", headers={"WWW-Authenticate": "Bearer"},
        )
    