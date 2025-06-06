from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.auth.models import Token
from app.core.auth.schemas import TokenPair, TokenData
from app.user.models import User

def get_or_create_google_user(db: Session, google_id: str, email: str, name: str) -> User:
    """
    Google OAuth 사용자를 조회하거나 생성합니다.
    
    Args:
        db (Session): 데이터베이스 세션
        google_id (str): Google OAuth sub ID
        email (str): 사용자 이메일
        name (str): 사용자 이름
    
    Returns:
        User: 조회되거나 생성된 사용자 객체
    """
    # 기존 사용자 조회
    user = db.query(User).filter_by(
        oauth_provider="google",
        oauth_sub=google_id
    ).first()
    
    if user:
        # 기존 사용자 정보 업데이트
        user.name = name
        user.email = email
        db.commit()
        db.refresh(user)
        return user
    
    # 새 사용자 생성
    user = User(
        name=name,
        email=email,
        oauth_provider="google",
        oauth_sub=google_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

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

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    """
    Access Token을 생성합니다.
    
    Args:
        data (dict): 토큰에 포함할 데이터
        expires_delta (timedelta): 토큰 만료 시간
    
    Returns:
        str: 생성된 Access Token
    """
    expire = datetime.utcnow() + expires_delta
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

def create_refresh_token(data: dict, expires_delta: timedelta) -> str:
    """
    Refresh Token을 생성합니다.
    
    Args:
        data (dict): 토큰에 포함할 데이터
        expires_delta (timedelta): 토큰 만료 시간
    
    Returns:
        str: 생성된 Refresh Token
    """
    expire = datetime.utcnow() + expires_delta
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