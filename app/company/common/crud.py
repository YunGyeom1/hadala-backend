from typing import Optional, List
from sqlalchemy.orm import Session
from app.company.common.models import Company, CompanyType
from uuid import UUID
from . import schemas
from app.profile.models import ProfileRole
from app.profile.crud import get_profile
from app.profile.models import Profile

def search_companies(
    db: Session,
    name: Optional[str] = None,
    company_type: Optional[CompanyType] = None,
    skip: int = 0,
    limit: int = 10
) -> List[Company]:
    """
    회사를 검색합니다.
    """
    query = db.query(Company)
    
    if name:
        query = query.filter(Company.name.ilike(f"%{name}%"))
    if company_type:
        query = query.filter(Company.type == company_type)
    
    return query.offset(skip).limit(limit).all()

def get_company_by_id(db: Session, company_id: UUID) -> Optional[Company]:
    """
    ID로 회사를 조회합니다.
    """
    return db.query(Company).filter(Company.id == company_id).first()

def get_company_by_name(db: Session, name: str) -> Optional[Company]:
    """
    이름으로 회사를 조회합니다.
    """
    return db.query(Company).filter(Company.name == name).first()

def create_company(
    db: Session,
    company: schemas.CompanyCreate,
    owner_id: UUID
) -> Company:
    """
    새로운 회사를 생성합니다.
    """
    db_company = Company(
        name=company.name,
        type=CompanyType.wholesaler,
        owner_id=owner_id
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def update_company(
    db: Session,
    company_id: UUID,
    company_update: schemas.CompanyUpdate
) -> Optional[Company]:
    """
    회사 정보를 업데이트합니다.
    """
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        return None

    update_data = company_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company

def update_company_owner(
    db: Session,
    company_id: UUID,
    new_owner_id: UUID
) -> Optional[Company]:
    """
    회사의 소유자를 변경합니다.
    """
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        return None

    db_company.owner_id = new_owner_id
    db.commit()
    db.refresh(db_company)
    return db_company

def add_company_user(
    db: Session,
    company_id: UUID,
    profile_id: UUID,
    role: ProfileRole
) -> Optional[Profile]:
    """
    회사에 사용자를 추가합니다.
    """
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        return None

    db_profile = get_profile(db, profile_id)
    if not db_profile:
        return None

    db_profile.role = role
    db_profile.company_id = company_id
    db.commit()
    db.refresh(db_profile)
    return db_profile

def remove_company_user(
    db: Session,
    company_id: UUID,
    profile_id: UUID
) -> Optional[Profile]:
    """
    회사에서 사용자를 제거합니다.
    """
    db_company = get_company_by_id(db, company_id)
    if not db_company:
        return None
    
    db_profile = get_profile(db, profile_id)
    if not db_profile:
        return None
    
    db_profile.company_id = None
    db_profile.role = None
    db.commit()
    db.refresh(db_profile)
    return db_profile
