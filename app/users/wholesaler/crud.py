from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.users.wholesaler.models import Wholesaler
from app.users.wholesaler.schemas import WholesalerCreate, WholesalerUpdateProfile, WholesalerUpdateCompanyInfo

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

def update_wholesaler_profile(
    db: Session,
    wholesaler_id: UUID,
    wholesaler_update: WholesalerUpdateProfile
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

def update_wholesaler_company_info(
    db: Session,
    wholesaler_id: UUID,
    wholesaler_update: WholesalerUpdateCompanyInfo
) -> Optional[Wholesaler]:
    """
    도매상의 회사 정보를 업데이트합니다.
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
