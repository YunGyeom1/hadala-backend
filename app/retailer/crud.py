from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
from typing import List, Optional

from app.retailer import models, schemas

def create_retailer(db: Session, retailer: schemas.RetailerCreate, user_id: Optional[UUID] = None) -> models.Retailer:
    db_retailer = models.Retailer(
        **retailer.model_dump(),
        user_id=user_id
    )
    db.add(db_retailer)
    db.commit()
    db.refresh(db_retailer)
    return db_retailer

def get_retailer(db: Session, retailer_id: UUID) -> Optional[models.Retailer]:
    return db.query(models.Retailer).filter(models.Retailer.id == retailer_id).first()

def get_retailer_by_user_id(db: Session, user_id: UUID) -> Optional[models.Retailer]:
    return db.query(models.Retailer).filter(models.Retailer.user_id == user_id).first()

def get_retailers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[schemas.RetailerFilter] = None
) -> List[models.Retailer]:
    query = db.query(models.Retailer)
    
    if filters:
        if filters.name:
            query = query.filter(models.Retailer.name.ilike(f"%{filters.name}%"))
        if filters.address:
            query = query.filter(models.Retailer.address.ilike(f"%{filters.address}%"))
    
    return query.offset(skip).limit(limit).all()

def update_retailer(
    db: Session,
    retailer_id: UUID,
    retailer_update: schemas.RetailerUpdate
) -> Optional[models.Retailer]:
    db_retailer = get_retailer(db, retailer_id)
    if not db_retailer:
        return None
    
    update_data = retailer_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_retailer, field, value)
    
    db.commit()
    db.refresh(db_retailer)
    return db_retailer 