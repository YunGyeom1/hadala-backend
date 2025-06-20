from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.profile.dependencies import get_current_profile
from app.database.session import get_db
from app.profile.models import Profile
from app.company.common import crud as common_crud
from . import schemas, crud

router = APIRouter(prefix="/companies/retail", tags=["retail"])

@router.post("/{company_id}/detail", response_model=schemas.RetailCompanyDetailResponse)
def create_retail_company_detail(
    company_id: UUID,
    detail: schemas.RetailCompanyDetailCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    소매회사 상세 정보를 생성합니다.
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
    
    return crud.create_retail_company_detail(db, company_id, detail)

@router.put("/{company_id}/detail", response_model=schemas.RetailCompanyDetailResponse)
def update_retail_company_detail(
    company_id: UUID,
    detail_update: schemas.RetailCompanyDetailUpdate,
    current_profile: Profile = Depends(get_current_profile),
    db: Session = Depends(get_db)
):
    """
    소매회사 상세 정보를 수정합니다.
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
    
    return crud.update_retail_company_detail(db, company_id, detail_update)

@router.get("/{company_id}/detail", response_model=schemas.RetailCompanyDetailResponse)
def get_retail_company_detail(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    소매회사 상세 정보를 조회합니다.
    """
    detail = crud.get_retail_company_detail(db, company_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="소매회사 상세 정보를 찾을 수 없습니다"
        )
    return detail 