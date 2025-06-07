from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database.session import get_db
from app.farmer import crud, schemas
from app.core.auth.dependencies import verify_access_token
from app.core.auth.schemas import VerifyTokenRequest

router = APIRouter(prefix="/farmers", tags=["farmers"])

@router.post("/", response_model=schemas.FarmerResponse)
def create_farmer(
    farmer: schemas.FarmerCreate,
    token: Optional[VerifyTokenRequest] = None,
    db: Session = Depends(get_db)
):
    """
    새로운 농부를 생성합니다.
    토큰이 제공된 경우 사용자와 연동됩니다.
    """
    user_id = None
    if token:
        # 토큰 검증 및 사용자 ID 추출
        token_data = verify_access_token(token.access_token)
        user_id = UUID(token_data.sub)
        
        # 이미 농부로 등록된 사용자인지 확인
        existing_farmer = crud.get_farmer_by_user_id(db, user_id)
        if existing_farmer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 농부로 등록된 사용자입니다"
            )
    
    return crud.create_farmer(db=db, farmer=farmer, user_id=user_id)

@router.get("/", response_model=List[schemas.FarmerResponse])
def get_farmers(
    skip: int = 0,
    limit: int = 100,
    filters: schemas.FarmerFilter = None,
    db: Session = Depends(get_db)
):
    """
    필터링된 농부 목록을 조회합니다.
    """
    return crud.get_farmers(db=db, skip=skip, limit=limit, filters=filters)

@router.get("/{farmer_id}", response_model=schemas.FarmerResponse)
def get_farmer(farmer_id: UUID, db: Session = Depends(get_db)):
    """
    ID로 농부를 조회합니다.
    """
    farmer = crud.get_farmer(db=db, farmer_id=farmer_id)
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="농부를 찾을 수 없습니다"
        )
    return farmer

@router.put("/{farmer_id}", response_model=schemas.FarmerResponse)
def update_farmer(
    farmer_id: UUID,
    farmer_update: schemas.FarmerUpdate,
    token: Optional[VerifyTokenRequest] = None,
    db: Session = Depends(get_db)
):
    """
    농부 정보를 업데이트합니다.
    user_id가 있는 경우, 해당 사용자만 수정할 수 있습니다.
    """
    # 농부 정보 조회
    farmer = crud.get_farmer(db=db, farmer_id=farmer_id)
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="농부를 찾을 수 없습니다"
        )
    
    # user_id가 있는 경우 권한 확인
    if farmer.user_id:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증이 필요합니다"
            )
        
        # 토큰 검증 및 사용자 ID 추출
        token_data = verify_access_token(token.access_token)
        user_id = UUID(token_data.sub)
        
        # 권한 확인
        if farmer.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 농부 정보를 수정할 권한이 없습니다"
            )
    
    return crud.update_farmer(db=db, farmer_id=farmer_id, farmer_update=farmer_update)