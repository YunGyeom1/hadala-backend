from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database.session import get_db
from app.retailer import crud, schemas
from app.core.auth.dependencies import verify_access_token
from app.core.auth.schemas import VerifyTokenRequest

router = APIRouter(prefix="/retailers", tags=["retailers"])

@router.post("/", response_model=schemas.RetailerResponse)
def create_retailer(
    retailer: schemas.RetailerCreate,
    token: Optional[VerifyTokenRequest] = None,
    db: Session = Depends(get_db)
):
    """
    새로운 소매상을 생성합니다.
    토큰이 제공된 경우 사용자와 연동됩니다.
    """
    user_id = None
    if token:
        # 토큰 검증 및 사용자 ID 추출
        token_data = verify_access_token(token.access_token)
        user_id = UUID(token_data.sub)
        
        # 이미 소매상으로 등록된 사용자인지 확인
        existing_retailer = crud.get_retailer_by_user_id(db, user_id)
        if existing_retailer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 소매상으로 등록된 사용자입니다"
            )
    
    return crud.create_retailer(db=db, retailer=retailer, user_id=user_id)

@router.get("/", response_model=List[schemas.RetailerResponse])
def get_retailers(
    skip: int = 0,
    limit: int = 100,
    filters: schemas.RetailerFilter = None,
    db: Session = Depends(get_db)
):
    """
    필터링된 소매상 목록을 조회합니다.
    """
    return crud.get_retailers(db=db, skip=skip, limit=limit, filters=filters)

@router.get("/{retailer_id}", response_model=schemas.RetailerResponse)
def get_retailer(retailer_id: UUID, db: Session = Depends(get_db)):
    """
    ID로 소매상을 조회합니다.
    """
    retailer = crud.get_retailer(db=db, retailer_id=retailer_id)
    if not retailer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="소매상을 찾을 수 없습니다"
        )
    return retailer

@router.put("/{retailer_id}", response_model=schemas.RetailerResponse)
def update_retailer(
    retailer_id: UUID,
    retailer_update: schemas.RetailerUpdate,
    token: Optional[VerifyTokenRequest] = None,
    db: Session = Depends(get_db)
):
    """
    소매상 정보를 업데이트합니다.
    user_id가 있는 경우, 해당 사용자만 수정할 수 있습니다.
    """
    # 소매상 정보 조회
    retailer = crud.get_retailer(db=db, retailer_id=retailer_id)
    if not retailer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="소매상을 찾을 수 없습니다"
        )
    
    # user_id가 있는 경우 권한 확인
    if retailer.user_id:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다"
            )
        
        # 토큰 검증 및 사용자 ID 추출
        token_data = verify_access_token(token.access_token)
        user_id = UUID(token_data.sub)
        
        # 권한 확인
        if retailer.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 소매상 정보를 수정할 권한이 없습니다"
            )
    
    return crud.update_retailer(db=db, retailer_id=retailer_id, retailer_update=retailer_update) 