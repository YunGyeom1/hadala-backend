from fastapi import HTTPException, Depends, status
from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC
from google.oauth2 import id_token
from google.auth.transport import requests
from app.core.config import settings

def create_token(data: dict, expires_delta: timedelta, secret: str, token_type: str) -> str:
    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.now(UTC) + expires_delta,
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

