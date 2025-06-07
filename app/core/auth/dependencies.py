from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.database.session import get_db
from app.core.config import settings
from .schemas import TokenData
from uuid import UUID
from app.user.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_access_token(token: str) -> TokenData:
    """
    Access Token을 검증합니다.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub: str = payload.get("sub")
        token_type: str = payload.get("token_type")
        
        if sub is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 Access Token입니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(sub=sub, token_type=token_type)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 Access Token입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    현재 인증된 사용자를 반환합니다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_access_token(token)
        user_id = UUID(token_data.sub)
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        return user
    except Exception:
        raise credentials_exception

def get_current_user_company_id(current_user):
    """
    현재 사용자의 회사 ID를 반환합니다.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="회사 소속이 아닙니다"
        )
    return current_user.company_id

def verify_company_affiliation(current_user):
    """
    사용자의 회사 소속을 확인합니다.
    """
    return get_current_user_company_id(current_user) 