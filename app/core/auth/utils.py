from fastapi import HTTPException, Depends, status
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID
from google.oauth2 import id_token
from google.auth.transport import requests
from app.database.session import get_db
from app.users.user.models import User
from app.core.config import settings

def create_token(data: dict, expires_delta: timedelta, secret: str, token_type: str) -> str:
    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.utcnow() + expires_delta,
        "token_type": token_type
    })
    return jwt.encode(to_encode, secret, algorithm=settings.ALGORITHM)


def create_access_token(data: dict) -> str:
    return create_token(data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), settings.SECRET_KEY, "access")


def create_refresh_token(data: dict) -> str:
    return create_token(data, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), settings.REFRESH_SECRET_KEY, "refresh")


def verify_token(token: str, secret: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
        if payload.get("token_type") != expected_type:
            raise ValueError("Token type mismatch")
        return payload
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"유효하지 않은 {expected_type.capitalize()} Token입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_access_token(token: str) -> dict:
    return verify_token(token, settings.SECRET_KEY, "access")


def verify_refresh_token(token: str) -> dict:
    return verify_token(token, settings.REFRESH_SECRET_KEY, "refresh")


def verify_google_id_token(id_token_str: str) -> dict:
    try:
        id_info = id_token.verify_oauth2_token(
            id_token_str, requests.Request(), settings.GOOGLE_CLIENT_ID
        )

        # aud 확인 (선택적이지만 보안상 강력 추천)
        if id_info['aud'] != settings.GOOGLE_CLIENT_ID:
            raise ValueError("잘못된 클라이언트 ID (aud mismatch)")
        return id_info

    except Exception:
        return None

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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )