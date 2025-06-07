from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.user.models import User
from typing import Optional, List
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.config import settings
from app.core.auth.dependencies import get_current_user
from .schemas import Token, TokenData
from app.company.models import Company
from app.center.models import CollectionCenter
from uuid import UUID

def get_current_user_company_id(current_user, db: Session) -> Optional[str]:
    """현재 사용자의 회사 ID를 반환합니다."""
    if current_user.wholesaler:
        return current_user.wholesaler.company_id
    return None

def verify_company_member(db: Session, user, company_id: str) -> bool:
    """
    사용자가 해당 회사의 멤버인지 확인합니다.
    """
    if user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사의 멤버가 아닙니다"
        )
    return True

def verify_company_role(db: Session, user, company_id: str, required_role: str) -> bool:
    """
    사용자가 해당 회사에서 필요한 역할을 가지고 있는지 확인합니다.
    """
    if user.company_id != company_id or user.role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다"
        )
    return True

def verify_center_member(db: Session, user, center_id: str) -> bool:
    """
    사용자가 해당 센터의 멤버인지 확인합니다.
    """
    center = db.query(CollectionCenter).filter(CollectionCenter.id == center_id).first()
    if not center or center.company_id != user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 센터의 멤버가 아닙니다"
        )
    return True

def get_company_member_dependency():
    """
    회사 멤버 확인을 위한 의존성 함수를 반환합니다.
    """
    def _verify_company_member(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ) -> bool:
        return verify_company_member(db, current_user, current_user.company_id)
    return _verify_company_member

def get_company_role_dependency(required_role: str):
    """
    회사 역할 확인을 위한 의존성 함수를 반환합니다.
    """
    def _verify_company_role(
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
    ) -> bool:
        return verify_company_role(db, current_user, current_user.company_id, required_role)
    return _verify_company_role

def verify_company_affiliation(current_user: User):
    if not getattr(current_user, 'company_id', None):
        raise HTTPException(status_code=403, detail="회사 소속이 아닙니다.")
    return current_user.company_id

def create_token_pair(data: dict) -> tuple[str, str]:
    """
    Access Token과 Refresh Token 쌍을 생성합니다.
    """
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    return access_token, refresh_token

def create_access_token(data: dict) -> str:
    """
    Access Token을 생성합니다.
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = Token(
        sub=data["sub"],
        token_type="access",
        exp=expire
    )
    
    to_encode = {
        "sub": token.sub,
        "exp": token.exp,
        "token_type": token.token_type,
        "jti": token.jti
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """
    Refresh Token을 생성합니다.
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token = Token(
        sub=data["sub"],
        token_type="refresh",
        exp=expire
    )
    
    to_encode = {
        "sub": token.sub,
        "exp": token.exp,
        "token_type": token.token_type,
        "jti": token.jti
    }
    
    return jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)

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

def verify_refresh_token(token: str) -> TokenData:
    """
    Refresh Token을 검증합니다.
    """
    try:
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub: str = payload.get("sub")
        token_type: str = payload.get("token_type")
        
        if sub is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 Refresh Token입니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(sub=sub, token_type=token_type)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 Refresh Token입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user_from_token(token: str, db: Session) -> User:
    """
    토큰에서 현재 사용자 정보를 가져옵니다.
    """
    try:
        token_data = verify_access_token(token)
        user_id = UUID(token_data.sub)
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증된 사용자를 찾을 수 없습니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        ) 