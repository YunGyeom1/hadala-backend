from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from fastapi import HTTPException, status
from app.company import models, schemas
from app.company.models import Company
from app.wholesaler.models import Wholesaler
from app.center.models import Center
from app.user.models import User
from app.company.models import Company



def get_company(db: Session, company_id: UUID) -> Company:
    return db.query(Company).filter(Company.id == company_id).first()

def get_companies(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> List[models.Company]:
    """
    회사 목록을 조회합니다.
    검색어가 있는 경우 이름, 사업자번호, 주소로 검색합니다.
    """
    query = db.query(models.Company)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Company.name.ilike(search_term),
                models.Company.description.ilike(search_term),
                models.Company.business_number.ilike(search_term),
                models.Company.address.ilike(search_term),
                models.Company.phone.ilike(search_term),
                models.Company.email.ilike(search_term),
            )
        )
    
    return query.offset(skip).limit(limit).all()


def create_company(
    db: Session,
    company: schemas.CompanyCreate,
    user_id: UUID
) -> models.Company:
    """
    새로운 회사를 생성합니다.
    """
    db_company = models.Company(
        name=company.name,
        description=company.description,
        business_number=company.business_number,
        address=company.address,
        phone=company.phone,
        email=company.email,
        owner=user_id
    )
    db.add(db_company)
    db.flush()  # ID를 얻기 위해 flush
    
    # 도매상의 company_id 업데이트
    wholesaler = db.query(Wholesaler).filter(Wholesaler.user_id == user_id).first()
    if wholesaler:
        wholesaler.company_id = db_company.id
        db.flush()
        db.refresh(wholesaler)
    
    db.commit()
    db.refresh(db_company)
    return db_company


def update_company(
    db: Session,
    company_id: UUID,
    company_update: schemas.CompanyUpdate
) -> Optional[models.Company]:
    """
    회사 정보를 업데이트합니다.
    """
    db_company = get_company(db, company_id)
    if not db_company:
        return None
        
    update_data = company_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company


def get_company_wholesalers(
    db: Session,
    company_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Wholesaler]:
    """
    회사 소속 도매상 목록을 조회합니다.
    """
    return db.query(Wholesaler)\
        .filter(Wholesaler.company_id == company_id)\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_company_centers(
    db: Session,
    company_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Center]:
    """
    회사 소유 집하장 목록을 조회합니다.
    """
    return db.query(Center)\
        .filter(Center.company_id == company_id)\
        .offset(skip)\
        .limit(limit)\
        .all() 

def get_role(db: Session, user: User, company_id: UUID) -> Optional[str]:
    """
    사용자의 회사 내 역할을 반환합니다.
    소속이 없으면 None 반환.
    """
    wholesaler = db.query(Wholesaler).filter(
        Wholesaler.user_id == user.id,
        Wholesaler.company_id == company_id
    ).first()

    if wholesaler:
        return wholesaler.role  # 'owner', 'manager', 'staff' 등
    return None