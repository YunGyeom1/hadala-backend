from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database.session import get_db
from app.profile.dependencies import get_current_profile
from app.profile.models import Profile
from . import crud, schemas

router = APIRouter(prefix="/centers", tags=["centers"])

@router.put("/{center_id}", response_model=schemas.CenterUpdate)
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