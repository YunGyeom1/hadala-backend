from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.company.detail.farmer.models import FarmerCompanyDetail
from . import schemas
from datetime import date, timedelta

def create_farmer_company_detail(
    db: Session,
    company_id: UUID,
    detail: schemas.FarmerCompanyDetailCreate
) -> FarmerCompanyDetail:
    """
    농장 상세 정보를 생성합니다.
    """
    db_detail = FarmerCompanyDetail(
        company_id=company_id,
        **detail.model_dump()
    )
    db.add(db_detail)
    db.commit()
    db.refresh(db_detail)
    return db_detail

def get_farmer_company_detail(
    db: Session,
    company_id: UUID
) -> Optional[FarmerCompanyDetail]:
    """
    농장 상세 정보를 조회합니다.
    """
    return db.query(FarmerCompanyDetail).filter(
        FarmerCompanyDetail.company_id == company_id
    ).first()

def update_farmer_company_detail(
    db: Session,
    company_id: UUID,
    detail_update: schemas.FarmerCompanyDetailUpdate
) -> Optional[FarmerCompanyDetail]:
    """
    농장 상세 정보를 업데이트합니다.
    """
    db_detail = get_farmer_company_detail(db, company_id)
    if not db_detail:
        return None

    update_data = detail_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_detail, field, value)
    
    db.commit()
    db.refresh(db_detail)
    return db_detail 