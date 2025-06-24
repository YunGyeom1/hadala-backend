from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.database.session import get_db
from app.profile.dependencies import get_current_profile
from app.profile.models import Profile
from . import crud, schemas

router = APIRouter(prefix="/centers", tags=["centers"])

@router.post("/", response_model=schemas.CenterResponse)
def create_center(
    center_create: schemas.CenterCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    새로운 센터를 생성합니다.
    """
    if not current_profile.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회사에 속해있지 않습니다"
        )
    
    return crud.create_center(db, current_profile.company_id, center_create)

@router.get("/", response_model=List[schemas.CenterResponse])
def get_centers(
    company_id: UUID = Query(None, description="회사 ID"),
    skip: int = Query(0, ge=0, description="건너뛸 결과 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 결과 수"),
    db: Session = Depends(get_db)
):
    """
    센터 목록을 조회합니다.
    """
    return crud.get_centers(db, company_id, skip, limit)

@router.get("/{center_id}", response_model=schemas.CenterResponse)
def get_center(
    center_id: UUID,
    db: Session = Depends(get_db)
):
    """
    특정 센터를 조회합니다.
    """
    center = crud.get_center_by_id(db, center_id)
    if not center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="센터를 찾을 수 없습니다"
        )
    return center

@router.put("/{center_id}", response_model=schemas.CenterResponse)
def update_center(
    center_id: UUID,
    center_update: schemas.CenterUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    센터 정보를 업데이트합니다.
    """
    db_center = crud.get_center_by_id(db, center_id)
    if not db_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="센터를 찾을 수 없습니다"
        )
    
    # 회사 소유자나 센터 매니저만 수정 가능
    if current_profile.company_id != db_center.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 센터에 대한 수정 권한이 없습니다"
        )
    
    if current_profile.id != db_center.company.owner_id and current_profile.id != db_center.manager_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 센터에 대한 수정 권한이 없습니다"
        )
    
    updated_center = crud.update_center(db, center_id, center_update)
    if not updated_center:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="센터 정보 업데이트에 실패했습니다"
        )
    
    return updated_center 