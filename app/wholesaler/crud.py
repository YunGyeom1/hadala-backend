from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.wholesaler.models import Wholesaler
from app.wholesaler.schemas import WholesalerCreate, WholesalerUpdate, WholesalerRoleUpdate
from app.company.models import Company

def get_wholesaler(db: Session, wholesaler_id: UUID) -> Optional[Wholesaler]:
    """
    ID로 도매상을 조회합니다.
    """
    return db.query(Wholesaler).filter(Wholesaler.id == wholesaler_id).first()

def get_wholesaler_by_user_id(db: Session, user_id: UUID) -> Optional[Wholesaler]:
    """
    사용자 ID로 도매상을 조회합니다.
    """
    return db.query(Wholesaler).filter(Wholesaler.user_id == user_id).first()

def create_wholesaler(db: Session, wholesaler: WholesalerCreate) -> Wholesaler:
    """
    새로운 도매상을 생성합니다.
    """
    db_wholesaler = Wholesaler(**wholesaler.model_dump())
    db.add(db_wholesaler)
    db.commit()
    db.refresh(db_wholesaler)
    return db_wholesaler

def update_wholesaler(
    db: Session,
    wholesaler_id: UUID,
    wholesaler_update: WholesalerUpdate
) -> Optional[Wholesaler]:
    """
    도매상 정보를 업데이트합니다.
    """
    db_wholesaler = get_wholesaler(db, wholesaler_id)
    if not db_wholesaler:
        return None
    
    update_data = wholesaler_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_wholesaler, field, value)
    
    db.commit()
    db.refresh(db_wholesaler)
    return db_wholesaler

def update_wholesaler_role(
    db: Session,
    wholesaler_id: UUID,
    role_update: WholesalerRoleUpdate
) -> Optional[Wholesaler]:
    """
    도매상의 역할을 업데이트합니다.
    """
    db_wholesaler = get_wholesaler(db, wholesaler_id)
    if not db_wholesaler:
        return None
    
    db_wholesaler.role = role_update.role
    db.commit()
    db.refresh(db_wholesaler)
    return db_wholesaler

def update_company_owner(
    db: Session,
    company_id: UUID,
    new_owner_id: UUID
) -> Optional[Company]:
    """
    회사의 오너를 변경합니다.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return None
    
    company.owner = new_owner_id
    db.commit()
    db.refresh(company)
    return company

def remove_wholesaler_from_company(
    db: Session,
    wholesaler_id: UUID
) -> Optional[Wholesaler]:
    """
    도매상을 회사에서 제거합니다.
    """
    db_wholesaler = get_wholesaler(db, wholesaler_id)
    if not db_wholesaler:
        return None
    
    # 회사 오너인 경우 회사 오너도 제거
    company = db.query(Company).filter(Company.owner == wholesaler_id).first()
    if company:
        company.owner = None
    
    db_wholesaler.company_id = None
    db_wholesaler.role = None
    db.commit()
    db.refresh(db_wholesaler)
    return db_wholesaler

def get_company_wholesalers(
    db: Session,
    company_id: UUID
) -> List[Wholesaler]:
    """
    회사 소속 도매상 목록을 조회합니다.
    """
    return db.query(Wholesaler).filter(Wholesaler.company_id == company_id).all()