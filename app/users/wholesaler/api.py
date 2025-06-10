from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database.session import get_db
from app.users.wholesaler import crud, schemas
from app.core.auth.utils import get_current_user
from app.users.user.models import User

router = APIRouter(prefix="/users/wholesaler", tags=["wholesaler"])

# 도매상 생성
@router.post("", response_model=schemas.WholesalerResponse)
def create_wholesaler(
    wholesaler_create: schemas.WholesalerCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.WholesalerResponse:
    # 이미 도매상으로 등록된 사용자인지 확인
    existing_wholesaler = crud.get_wholesaler_by_user_id(db, user.id)
    if existing_wholesaler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 도매상으로 등록된 사용자입니다"
        )
    
    # user_id를 현재 로그인한 사용자의 ID로 설정
    wholesaler_create.user_id = user.id
    return crud.create_wholesaler(db=db, wholesaler=wholesaler_create)

# 내 도매상 정보 조회
@router.get("/me", response_model=schemas.WholesalerResponse)
def get_my_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.WholesalerResponse:
    wholesaler = crud.get_wholesaler_by_user_id(db, current_user.id)
    if not wholesaler:
        raise HTTPException(status_code=404, detail="도매상 정보를 찾을 수 없습니다")
    return wholesaler

# 내 도매상 정보 수정
@router.put("/me", response_model=schemas.WholesalerResponse)
def update_my_info(
    wholesaler_update: schemas.WholesalerUpdateProfile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.WholesalerResponse:
    wholesaler = crud.get_wholesaler_by_user_id(db, user.id)
    if not wholesaler:
        raise HTTPException(status_code=404, detail="도매상 정보를 찾을 수 없습니다")
    return crud.update_wholesaler_profile(db=db, wholesaler_id=wholesaler.id, wholesaler_update=wholesaler_update)

# 특정 도매상 정보 조회(같은 회사 소속 도매상만 조회 가능)
@router.get("/{wholesaler_id}", response_model=schemas.WholesalerResponse)
def get_wholesaler(
    wholesaler_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.WholesalerResponse:
    # 요청자의 도매상 정보 조회
    requester = crud.get_wholesaler_by_user_id(db, user.id)
    if not requester:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="도매상만 조회할 수 있습니다"
        )
    
    # 대상 도매상 정보 조회
    target = crud.get_wholesaler(db, wholesaler_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="도매상을 찾을 수 없습니다"
        )
    
    # 같은 회사 소속인지 확인
    if requester.company_id != target.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="같은 회사 소속 도매상만 조회할 수 있습니다"
        )
    
    return target

