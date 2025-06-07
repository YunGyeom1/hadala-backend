from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database.session import get_db
from app.retailer import crud, schemas
from app.core.auth.utils import get_current_user
from app.user.models import User 

router = APIRouter(prefix="/retailers", tags=["retailers"])

@router.post("/", response_model=schemas.RetailerOut)
def create_retailer(
    retailer: schemas.RetailerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ✅ 인증된 사용자만 가능
):
    user_id = current_user.id

    existing = crud.get_retailer_by_user_id(db, user_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="이미 소매상으로 등록된 사용자입니다"
        )

    return crud.create_retailer(db=db, retailer=retailer, user_id=user_id)

@router.get("/", response_model=List[schemas.RetailerOut])
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

@router.get("/{retailer_id}", response_model=schemas.RetailerOut)
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

@router.put("/{retailer_id}", response_model=schemas.RetailerOut)
def update_retailer(
    retailer_id: UUID,
    retailer_update: schemas.RetailerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    retailer = crud.get_retailer(db, retailer_id)
    if not retailer:
        raise HTTPException(status_code=404, detail="소매상을 찾을 수 없습니다")

    if retailer.user_id and retailer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="해당 소매상 정보를 수정할 권한이 없습니다")

    return crud.update_retailer(db=db, retailer_id=retailer_id, retailer_update=retailer_update)