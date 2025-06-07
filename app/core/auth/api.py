from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.auth import schemas, utils
from app.user import crud

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google-login", response_model=schemas.GoogleOAuthLoginResponse)
async def google_login(data: schemas.GoogleOAuthLoginRequest, db: Session = Depends(get_db)):
    user_info = utils.verify_google_id_token(data.id_token)
    if not user_info:
        raise HTTPException(status_code=400, detail="유효하지 않은 ID 토큰입니다")

    user = crud.get_or_create_user_by_oauth(db, user_info)
    access_token = utils.create_access_token({"sub": str(user.id)})
    refresh_token = utils.create_refresh_token({"sub": str(user.id)})

    return schemas.GoogleOAuthLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id)
    )

@router.post("/verify", response_model=schemas.VerifyTokenResponse)
async def verify_access_token(data: schemas.VerifyTokenRequest):
    try:
        token_data = utils.verify_access_token(data.access_token)
        return schemas.VerifyTokenResponse(valid=True, user_id=token_data["sub"])
    except Exception as e:
        return schemas.VerifyTokenResponse(valid=False, error=str(e))


@router.post("/refresh", response_model=schemas.RefreshTokenResponse)
async def refresh_token(data: schemas.RefreshTokenRequest):
    try:
        token_data = utils.verify_refresh_token(data.refresh_token)
        new_access_token = utils.create_access_token({"sub": token_data["sub"]})
        return schemas.RefreshTokenResponse(access_token=new_access_token)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Refresh token 오류: {str(e)}",
        )