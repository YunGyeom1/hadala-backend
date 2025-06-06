from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from fastapi import HTTPException, status
from pydantic import BaseModel
import uuid
from app.core.config import settings

class TokenData(BaseModel):
    sub: Optional[str] = None
    token_type: Optional[str] = None

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

def create_token_pair(data: dict) -> TokenPair:
    """
    Access Token과 Refresh Token 쌍을 생성합니다.
    
    Args:
        data (dict): 토큰에 포함할 데이터
    
    Returns:
        TokenPair: 생성된 토큰 쌍
    """
    # Access Token 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=data,
        expires_delta=access_token_expires
    )
    
    # Refresh Token 생성
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data=data,
        expires_delta=refresh_token_expires
    )
    
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token
    )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Access Token을 생성합니다.
    
    Args:
        data (dict): 토큰에 포함할 데이터
        expires_delta (Optional[timedelta]): 토큰 만료 시간
    
    Returns:
        str: 생성된 Access Token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "token_type": "access",
        "jti": str(uuid.uuid4())  # JWT ID: 토큰의 고유 식별자
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Refresh Token을 생성합니다.
    
    Args:
        data (dict): 토큰에 포함할 데이터
        expires_delta (Optional[timedelta]): 토큰 만료 시간
    
    Returns:
        str: 생성된 Refresh Token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "token_type": "refresh",
        "jti": str(uuid.uuid4())  # JWT ID: 토큰의 고유 식별자
    })
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> TokenData:
    """
    Access Token을 검증합니다.
    
    Args:
        token (str): 검증할 Access Token
    
    Returns:
        TokenData: 검증된 토큰 데이터
    
    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
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
    
    Args:
        token (str): 검증할 Refresh Token
    
    Returns:
        TokenData: 검증된 토큰 데이터
    
    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
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