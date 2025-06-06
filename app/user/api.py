from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.session import get_db
from app.user import crud, schemas
from app.core.auth.crud import verify_access_token, verify_refresh_token, create_access_token
from app.core.auth.schemas import VerifyTokenRequest, RefreshTokenRequest, RefreshTokenResponse
from app.user.schemas import UserCreateOAuth, UserOut, OAuthResponse, OAuthError
from app.user.crud import get_or_create_oauth_user

router = APIRouter()

@router.get("/me", response_model=schemas.UserResponse)
def get_my_info(
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자의 정보를 조회합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 사용자 정보 조회
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    return user

@router.put("/me", response_model=schemas.UserResponse)
def update_my_info(
    user_update: schemas.UserUpdate,
    token: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자의 정보를 수정합니다.
    """
    # 토큰 검증 및 사용자 ID 추출
    token_data = verify_access_token(token.access_token)
    user_id = UUID(token_data.sub)
    
    # 사용자 정보 조회
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 정보 업데이트
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user 

@router.post("/oauth-login", response_model=OAuthResponse, responses={400: {"model": OAuthError}})
async def oauth_login(user_info: UserCreateOAuth, db: Session = Depends(get_db)):
    try:
        user, token_pair = get_or_create_oauth_user(db, user_info)
        return OAuthResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            user=user
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="OAuth 로그인 처리 중 오류가 발생했습니다."
        )

@router.post("/refresh", response_model=RefreshTokenResponse, responses={401: {"model": OAuthError}})
async def refresh_token(request: RefreshTokenRequest):
    try:
        # Refresh Token 검증
        token_data = verify_refresh_token(request.refresh_token)
        
        # 새로운 Access Token 생성
        access_token = create_access_token(data={"sub": token_data.sub})
        
        return RefreshTokenResponse(
            access_token=access_token
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="토큰 갱신 중 오류가 발생했습니다."
        )