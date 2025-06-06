from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from uuid import UUID

from app.center.models import CollectionCenter
from app.center.schemas import CenterCreate, CenterUpdate, CenterFilter

def create_center(db: Session, center: CenterCreate) -> CollectionCenter:
    """
    새로운 수집 센터를 생성합니다.
    """
    db_center = CollectionCenter(**center.model_dump())
    db.add(db_center)
    db.commit()
    db.refresh(db_center)
    return db_center

def get_center(db: Session, center_id: UUID) -> Optional[CollectionCenter]:
    """
    ID로 수집 센터를 조회합니다.
    """
    return db.query(CollectionCenter).filter(CollectionCenter.id == center_id).first()

def get_centers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[CenterFilter] = None
) -> List[CollectionCenter]:
    """
    수집 센터 목록을 조회합니다.
    필터링, 페이지네이션, 제한을 지원합니다.
    """
    query = db.query(CollectionCenter)
    
    if filters:
        conditions = []
        
        if filters.name:
            conditions.append(CollectionCenter.name.ilike(f"%{filters.name}%"))
        
        if filters.address:
            conditions.append(CollectionCenter.address.ilike(f"%{filters.address}%"))
        
        if filters.company_id:
            conditions.append(CollectionCenter.company_id == filters.company_id)
        
        if conditions:
            query = query.filter(and_(*conditions))
    
    return query.offset(skip).limit(limit).all()

def update_center(
    db: Session,
    center_id: UUID,
    center_update: CenterUpdate
) -> Optional[CollectionCenter]:
    """
    수집 센터 정보를 업데이트합니다.
    """
    db_center = get_center(db, center_id)
    if not db_center:
        return None
    
    update_data = center_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_center, field, value)
    
    db.commit()
    db.refresh(db_center)
    return db_center

def delete_center(db: Session, center_id: UUID) -> bool:
    """
    수집 센터를 삭제합니다.
    """
    db_center = get_center(db, center_id)
    if not db_center:
        return False
    
    db.delete(db_center)
    db.commit()
    return True

def get_center_wholesalers(
    db: Session,
    center_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[CollectionCenter]:
    """
    수집 센터에 등록된 도매상 목록을 조회합니다.
    """
    center = get_center(db, center_id)
    if not center:
        return []
    
    return center.wholesalers[skip:skip + limit] 