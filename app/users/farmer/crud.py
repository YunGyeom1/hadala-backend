from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.users.farmer.models import Farmer
from app.users.farmer.schemas import FarmerCreate, FarmerUpdate, FarmerFilter


def get_farmer_by_user_id(db: Session, user_id: UUID) -> Optional[Farmer]:
    return db.query(Farmer).filter(Farmer.user_id == user_id).first()


def create_farmer(db: Session, farmer: FarmerCreate, user_id: UUID) -> Farmer:
    db_farmer = Farmer(user_id=user_id, **farmer.model_dump())
    db.add(db_farmer)
    db.commit()
    db.refresh(db_farmer)
    return db_farmer


def get_farmer(db: Session, farmer_id: UUID) -> Optional[Farmer]:
    return db.query(Farmer).filter(Farmer.id == farmer_id).first()


def get_farmers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[FarmerFilter] = None
) -> List[Farmer]:
    query = db.query(Farmer)

    if filters:
        if filters.name:
            query = query.filter(Farmer.name.ilike(f"%{filters.name}%"))

        if filters.address:
            query = query.filter(Farmer.address.ilike(f"%{filters.address}%"))

        if filters.farm_size_m2_min is not None:
            query = query.filter(Farmer.farm_size_m2 >= filters.farm_size_m2_min)
        if filters.farm_size_m2_max is not None:
            query = query.filter(Farmer.farm_size_m2 <= filters.farm_size_m2_max)

        if filters.annual_output_kg_min is not None:
            query = query.filter(Farmer.annual_output_kg >= filters.annual_output_kg_min)
        if filters.annual_output_kg_max is not None:
            query = query.filter(Farmer.annual_output_kg <= filters.annual_output_kg_max)

        if filters.farm_members_min is not None:
            query = query.filter(Farmer.farm_members >= filters.farm_members_min)
        if filters.farm_members_max is not None:
            query = query.filter(Farmer.farm_members <= filters.farm_members_max)

    return query.offset(skip).limit(limit).all()


def update_farmer(db: Session, farmer_id: UUID, farmer_update: FarmerUpdate) -> Optional[Farmer]:
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
    db_farmer = get_farmer(db, farmer_id)
    if not db_farmer:
        return False

    db.delete(db_farmer)
    db.commit()
    return True