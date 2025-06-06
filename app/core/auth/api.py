from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.config import settings
from app.core.auth.schemas import (
    GoogleOAuthLoginRequest,
    GoogleOAuthLoginResponse,
    VerifyTokenRequest,
    VerifyTokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse
)
from app.core.auth.crud import (
    create_token_pair,
    verify_access_token,
    verify_refresh_token,
    get_or_create_google_user
)
from app.database.session import get_db

router = APIRouter()

@router.post("/google-login", response_model=GoogleOAuthLoginResponse)
async def google_login(
    request: GoogleOAuthLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Google OAuth2 로그인을 처리합니다.
    
    Args:
        request (GoogleOAuthLoginRequest): Google ID 토큰
        db (Session): 데이터베이스 세션
    
    Returns:
        GoogleOAuthLoginResponse: 액세스 토큰과 리프레시 토큰
    
    Raises:
        HTTPException: ID 토큰이 유효하지 않은 경우
    """
    try:
        # Google ID 토큰 검증
        idinfo = id_token.verify_oauth2_token(
            request.id_token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        # 사용자 정보 추출
        google_id = idinfo["sub"]
        email = idinfo["email"]
        name = idinfo.get("name", email.split("@")[0])
        
        # 사용자 조회 또는 생성
        user = get_or_create_google_user(db, google_id, email, name)
        
        # 토큰 생성
        token_data = {"sub": str(user.id)}
        tokens = create_token_pair(token_data)
        
        return GoogleOAuthLoginResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type="bearer",
            user_id=str(user.id)
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 Google ID 토큰입니다"
        )

@router.post("/verify", response_model=VerifyTokenResponse)
async def verify_token(request: VerifyTokenRequest):
    """
    Access Token을 검증합니다.
    
    Args:
        request (VerifyTokenRequest): 검증할 Access Token
    
    Returns:
        VerifyTokenResponse: 토큰 검증 결과
    """
    try:
        token_data = verify_access_token(request.access_token)
        return VerifyTokenResponse(
            valid=True,
            user_id=token_data.sub
        )
    except HTTPException:
        return VerifyTokenResponse(
            valid=False,
            error="유효하지 않은 토큰입니다"
        )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh Token을 사용하여 새로운 Access Token을 발급합니다.
    
    Args:
        request (RefreshTokenRequest): Refresh Token
    
    Returns:
        RefreshTokenResponse: 새로운 Access Token
    
    Raises:
        HTTPException: Refresh Token이 유효하지 않은 경우
    """
    try:
        # Refresh Token 검증
        token_data = verify_refresh_token(request.refresh_token)
        
        # 새로운 Access Token 생성
        tokens = create_token_pair({"sub": token_data.sub})
        
        return RefreshTokenResponse(
            access_token=tokens.access_token,
            token_type="bearer"
        )
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 Refresh Token입니다"
        )