from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.auth import schemas, utils, crud

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google-login", response_model=schemas.GoogleOAuthLoginResponse)
async def google_login(data: schemas.GoogleOAuthLoginRequest, db: Session = Depends(get_db)):
    user_info = utils.verify_google_id_token(data.id_token)
    if not user_info:
        raise HTTPException(status_code=400, detail="유효하지 않은 ID 토큰입니다")

    if not user_info.get("email_verified"):
        raise HTTPException(status_code=400, detail="이메일 인증되지 않은 계정입니다")

    user = crud.get_user_by_oauth(db, provider="google", sub=user_info["sub"])
    if not user:
        user = crud.create_user_by_google_oauth(db, user_info)

    access_token = utils.create_access_token({"sub": str(user.id)})
    refresh_token = utils.create_refresh_token({"sub": str(user.id)})

    return schemas.GoogleOAuthLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/verify", response_model=schemas.VerifyRefreshTokenResponse)
async def verify_refresh_token(data: schemas.VerifyRefreshTokenRequest):
    try:
        token_data = utils.verify_refresh_token(data.refresh_token)
        return schemas.VerifyRefreshTokenResponse(valid=True)
    except Exception as e:
        return schemas.VerifyRefreshTokenResponse(valid=False, error=str(e))


@router.post("/refresh", response_model=schemas.AccessTokenResponse)
async def refresh_token(data: schemas.AccessTokenRequest):
    try:
        token_data = utils.verify_refresh_token(data.refresh_token)
        new_access_token = utils.create_access_token({"sub": token_data["sub"]})
        return schemas.AccessTokenResponse(access_token=new_access_token)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Refresh token 오류: {str(e)}",
        )