from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from uuid import UUID

from app.company.models import Company
from app.company.schemas import CompanyCreate, CompanyUpdate, CompanyFilter

def create_company(db: Session, company: CompanyCreate, owner_id: UUID) -> Company:
    """
    새로운 회사를 생성합니다.
    """
    db_company = Company(
        **company.model_dump(),
        owner=owner_id
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def get_company(db: Session, company_id: UUID) -> Optional[Company]:
    """
    ID로 회사를 조회합니다.
    """
    return db.query(Company).filter(Company.id == company_id).first()

def get_companies(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[CompanyFilter] = None
) -> List[Company]:
    """
    필터링된 회사 목록을 조회합니다.
    """
    query = db.query(Company)
    
    if filters:
        if filters.name:
            query = query.filter(Company.name.ilike(f"%{filters.name}%"))
        if filters.has_owner is not None:
            if filters.has_owner:
                query = query.filter(Company.owner.isnot(None))
            else:
                query = query.filter(Company.owner.is_(None))
    
    return query.offset(skip).limit(limit).all()

def update_company(
    db: Session,
    company_id: UUID,
    company_update: CompanyUpdate
) -> Optional[Company]:
    """
    회사 정보를 업데이트합니다.
    """
    db_company = get_company(db, company_id)
    if not db_company:
        return None
    
    update_data = company_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company

def get_company_wholesalers(
    db: Session,
    company_id: UUID
) -> List[Company]:
    """
    회사 소속 도매상 목록을 조회합니다.
    """
    company = get_company(db, company_id)
    if not company:
        return []
    return company.wholesalers

def get_company_collection_centers(
    db: Session,
    company_id: UUID
) -> List[Company]:
    """
    회사 소유 집하장 목록을 조회합니다.
    """
    company = get_company(db, company_id)
    if not company:
        return []
    return company.centers