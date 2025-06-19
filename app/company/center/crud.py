from sqlalchemy.orm import Session
from uuid import UUID
from . import models, schemas
from app.profile.crud import get_profile
from app.transactions.shipment import crud as retail_crud
from app.transactions.shipment import crud as wholesale_crud
from datetime import date, Optional

def get_center_by_id(db: Session, center_id: UUID):
    """
    ID로 센터를 조회합니다.
    """
    return db.query(models.Center).filter(models.Center.id == center_id).first()

def get_center_by_name(db: Session, center_name: str):
    """
    이름으로 센터를 조회합니다.
    """
    return db.query(models.Center).filter(models.Center.name == center_name).first()

def update_center(
    db: Session,
    center_id: UUID,
    center_update: schemas.CenterUpdate
):
    """
    센터 정보를 업데이트합니다.
    """
    db_center = get_center_by_id(db, center_id)
    if not db_center:
        return None
    
    # 매니저 프로필이 변경되는 경우 프로필 존재 여부 확인
    if center_update.manager_profile_id:
        profile = get_profile(db, center_update.manager_profile_id)
        if not profile:
            return None
    
    update_data = center_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_center, field, value)
    
    db.commit()
    db.refresh(db_center)
    return db_center 

def create_center(
    db: Session,
    company_id: UUID,
    center_create: schemas.CenterCreate
):
    """
    센터를 생성합니다.
    """
    db_center = models.Center(
        name=center_create.name,
        company_id=company_id
    )
    db.add(db_center)
    db.commit()
    db.refresh(db_center)
    return db_center

def remove_center(
    db: Session,
    center_id: UUID
):
    """
    센터를 삭제합니다.
    """
    db_center = get_center_by_id(db, center_id)
    if not db_center:
        return None
    db.delete(db_center)
    db.commit()
    return db_center

def get_first_shipment_date_from_center(db: Session, center_id: UUID) -> Optional[date]:
    """
    센터의 가장 첫 영수증 날짜를 조회합니다.
    """
    # retail shipment의 가장 첫 날짜 조회
    first_retail = db.query(retail_crud.models.shipment)\
        .filter(retail_crud.models.shipment.center_id == center_id)\
        .order_by(retail_crud.models.shipment.created_at.asc())\
        .first()
    
    # wholesale shipment의 가장 첫 날짜 조회
    first_wholesale = db.query(wholesale_crud.models.shipment)\
        .filter(wholesale_crud.models.shipment.center_id == center_id)\
        .order_by(wholesale_crud.models.shipment.created_at.asc())\
        .first()
    
    # 두 날짜 중 더 이른 날짜 반환
    if first_retail and first_wholesale:
        return min(first_retail.created_at.date(), first_wholesale.created_at.date())
    elif first_retail:
        return first_retail.created_at.date()
    elif first_wholesale:
        return first_wholesale.created_at.date()
    return None
