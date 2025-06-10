from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database.session import get_db
from app.wholesale_company.center import crud, schemas
from app.core.auth.utils import get_current_user
from app.users.user.models import User
from app.wholesale_company.center.utils import check_center_permission

router = APIRouter(prefix="/centers", tags=["centers"])

@router.post("", response_model=schemas.CenterResponse)
def create_center(
    center: schemas.CenterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    새로운 수집 센터를 생성합니다.
    """
    # 회사 오너 권한 확인
    check_center_permission(db, current_user, company_id=center.company_id, allowed_roles=["owner"])
    return crud.create_center(db=db, center=center)

@router.get("", response_model=List[schemas.CenterResponse])
def get_centers(
    skip: int = 0,
    limit: int = 100,
    filters: schemas.CenterFilter = None,
    db: Session = Depends(get_db)
):
    """
    수집 센터 목록을 조회합니다.
    """
    return crud.get_centers(db, skip, limit, filters)

@router.get("/{center_id}", response_model=schemas.CenterResponse)
def read_center(
    center_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 수집 센터의 정보를 조회합니다.
    """
    return check_center_permission(db, current_user, center_id=center_id, allowed_roles=["owner", "manager", "member"])

@router.put("/{center_id}", response_model=schemas.CenterResponse)
def update_center(
    center_id: UUID,
    center_update: schemas.CenterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    수집 센터 정보를 업데이트합니다.
    """
    check_center_permission(db, current_user, center_id=center_id, allowed_roles=["owner"])
    return crud.update_center(db=db, center_id=center_id, center_update=center_update)

@router.delete("/{center_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_center(
    center_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    수집 센터를 삭제합니다.
    """
    check_center_permission(db, current_user, center_id=center_id, allowed_roles=["owner"])
    crud.delete_center(db=db, center_id=center_id)
    return None

@router.get("/{center_id}/wholesalers", response_model=List[schemas.WholesalerInCenter])
def get_center_wholesalers(
    center_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    수집 센터에 등록된 도매상 목록을 조회합니다.
    """
    check_center_permission(db, current_user, center_id=center_id, allowed_roles=["owner", "manager", "member"])
    return crud.get_center_wholesalers(db, center_id, skip, limit)