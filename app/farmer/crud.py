from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from uuid import UUID

from app.farmer.models import Farmer
from app.farmer.schemas import FarmerCreate, FarmerUpdate, FarmerFilter

def get_farmer_by_user_id(db: Session, user_id: UUID) -> Optional[Farmer]:
    """
    사용자 ID로 농부를 조회합니다.
    """
    return db.query(Farmer).filter(Farmer.user_id == user_id).first()

def create_farmer(db: Session, farmer: FarmerCreate, user_id: UUID) -> Farmer:
    """
    새로운 농부를 생성합니다.
    """
    db_farmer = Farmer(
        user_id=user_id,
        **farmer.model_dump()
    )
    db.add(db_farmer)
    db.commit()
    db.refresh(db_farmer)
    return db_farmer

def get_farmer(db: Session, farmer_id: UUID) -> Optional[Farmer]:
    """
    ID로 농부를 조회합니다.
    """
    return db.query(Farmer).filter(Farmer.id == farmer_id).first()

def get_farmers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[FarmerFilter] = None
) -> List[Farmer]:
    """
    필터링된 농부 목록을 조회합니다.
    """
    query = db.query(Farmer)
    
    if filters:
        if filters.address:
            query = query.filter(Farmer.address.ilike(f"%{filters.address}%"))
        
        # 농장 크기 필터링
        if filters.farm_size_m2_min is not None:
            query = query.filter(Farmer.farm_size_m2 >= filters.farm_size_m2_min)
        if filters.farm_size_m2_max is not None:
            query = query.filter(Farmer.farm_size_m2 <= filters.farm_size_m2_max)
        
        # 연간 생산량 필터링
        if filters.annual_output_kg_min is not None:
            query = query.filter(Farmer.annual_output_kg >= filters.annual_output_kg_min)
        if filters.annual_output_kg_max is not None:
            query = query.filter(Farmer.annual_output_kg <= filters.annual_output_kg_max)
        
        # 농장 구성원 수 필터링
        if filters.farm_members_min is not None:
            query = query.filter(Farmer.farm_members >= filters.farm_members_min)
        if filters.farm_members_max is not None:
            query = query.filter(Farmer.farm_members <= filters.farm_members_max)
    
    return query.offset(skip).limit(limit).all()

def update_farmer(
    db: Session,
    farmer_id: UUID,
    farmer_update: FarmerUpdate
) -> Optional[Farmer]:
    """
    농부 정보를 업데이트합니다.
    """
    db_farmer = get_farmer(db, farmer_id)
    if not db_farmer:
        return None
    
    update_data = farmer_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_farmer, field, value)
    
    db.commit()
    db.refresh(db_farmer)
    return db_farmer

def delete_farmer(db: Session, farmer_id: UUID) -> bool:
    """
    농부를 삭제합니다.
    """
    db_farmer = get_farmer(db, farmer_id)
    if not db_farmer:
        return False
    
    db.delete(db_farmer)
    db.commit()
    return True