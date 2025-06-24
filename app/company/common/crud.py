from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from app.company.common.models import Company, CompanyType
from uuid import UUID
from . import schemas
from app.profile.models import ProfileRole
from app.profile.crud import get_profile
from app.profile.models import Profile
from app.company.detail.wholesale.crud import create_wholesale_company_detail
from app.company.detail.wholesale.schemas import WholesaleCompanyDetailCreate
from app.company.detail.retail.crud import create_retail_company_detail
from app.company.detail.retail.schemas import RetailCompanyDetailCreate
from app.company.detail.farmer.crud import create_farmer_company_detail
from app.company.detail.farmer.schemas import FarmerCompanyDetailCreate

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
        type=company.type,
        owner_id=owner_id
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    # 소유자를 회사 멤버로 자동 추가
    try:
        owner_profile = get_profile(db, owner_id)
        if owner_profile:
            owner_profile.company_id = db_company.id
            owner_profile.role = ProfileRole.owner
            db.commit()
            db.refresh(owner_profile)
    except Exception as e:
        print(f"Error adding owner to company: {e}")
    
    # 회사 타입에 따라 상세 정보 자동 생성
    try:
        if company.type == CompanyType.WHOLESALER:
            # 도매상 상세 정보 생성 (기본값 사용)
            default_detail = WholesaleCompanyDetailCreate()
            wholesale_detail = create_wholesale_company_detail(db, db_company.id, default_detail)
            db_company.wholesale_company_detail_id = wholesale_detail.id
            
        elif company.type == CompanyType.RETAILER:
            # 소매상 상세 정보 생성 (기본값 사용)
            default_detail = RetailCompanyDetailCreate()
            retail_detail = create_retail_company_detail(db, db_company.id, default_detail)
            db_company.retail_company_detail_id = retail_detail.id
            
        elif company.type == CompanyType.FARMER:
            # 농가 상세 정보 생성 (기본값 사용)
            default_detail = FarmerCompanyDetailCreate()
            farmer_detail = create_farmer_company_detail(db, db_company.id, default_detail)
            db_company.farmer_company_detail_id = farmer_detail.id
            
        db.commit()
        db.refresh(db_company)
        
    except Exception as e:
        print(f"Error creating company detail: {e}")
        # detail 생성 실패해도 회사는 생성됨
    
    return db_company

def search_companies(db: Session, name: Optional[str] = None, company_type: Optional[CompanyType] = None, skip: int = 0, limit: int = 10) -> List[Company]:
    """
    회사를 검색합니다.
    """
    query = db.query(Company).options(joinedload(Company.owner))
    
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

def get_company_users(
    db: Session,
    company_id: UUID
) -> List[Profile]:
    """
    회사에 속한 사용자 목록을 조회합니다.
    """
    return db.query(Profile).filter(Profile.company_id == company_id).all()
