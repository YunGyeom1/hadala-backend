from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.profile.dependencies import get_current_profile
from app.database.session import get_db
from app.profile.models import Profile
from app.company.common import crud as common_crud
from . import schemas, crud

router = APIRouter(prefix="/companies/wholesale", tags=["wholesale"])

@router.post("/{company_id}/detail", response_model=schemas.WholesaleCompanyDetailResponse)
def create_wholesale_company_detail(
    company_id: UUID,
    detail: schemas.WholesaleCompanyDetailCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    도매회사 상세 정보를 생성합니다.
    """
    company = common_crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    if company.owner_id != current_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사에 대한 접근 권한이 없습니다"
        )
    
    return crud.create_wholesale_company_detail(db, company_id, detail)

@router.put("/{company_id}/detail", response_model=schemas.WholesaleCompanyDetailResponse)
def update_wholesale_company_detail(
    company_id: UUID,
    detail_update: schemas.WholesaleCompanyDetailUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    도매회사 상세 정보를 수정합니다.
    """
    company = common_crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    if company.owner_id != current_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 회사에 대한 수정 권한이 없습니다"
        )
    
    return crud.update_wholesale_company_detail(db, company_id, detail_update)

@router.get("/{company_id}/detail", response_model=schemas.WholesaleCompanyDetailResponse)
def get_wholesale_company_detail(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    도매회사 상세 정보를 조회합니다.
    """
    # 먼저 회사가 존재하는지 확인
    company = common_crud.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다"
        )
    
    detail = crud.get_wholesale_company_detail(db, company_id)
    if not detail:
        # 상세 정보가 없으면 자동으로 생성
        try:
            default_detail = schemas.WholesaleCompanyDetailCreate()
            detail = crud.create_wholesale_company_detail(db, company_id, default_detail)
            
            # 회사의 wholesale_company_detail_id 업데이트
            company.wholesale_company_detail_id = detail.id
            db.commit()
            db.refresh(detail)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"상세 정보 생성에 실패했습니다: {str(e)}"
            )
    
    return detail