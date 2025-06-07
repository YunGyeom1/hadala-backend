from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database.session import get_db
from app.farmer import crud, schemas
from app.core.auth.utils import get_current_user
from app.user.models import User

router = APIRouter(prefix="/farmers", tags=["farmers"])


@router.post("/", response_model=schemas.FarmerResponse)
def create_farmer(
    farmer: schemas.FarmerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    새로운 농부를 생성합니다. 인증된 사용자와 연동됩니다.
    """
    user_id = current_user.id

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
    filters: schemas.FarmerFilter = Depends(),
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    농부 정보를 업데이트합니다. 인증된 사용자만 자신의 정보 수정 가능.
    """
    farmer = crud.get_farmer(db=db, farmer_id=farmer_id)
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="농부를 찾을 수 없습니다"
        )

    # 권한 확인
    if farmer.user_id and farmer.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 농부 정보를 수정할 권한이 없습니다"
        )

    return crud.update_farmer(db=db, farmer_id=farmer_id, farmer_update=farmer_update)