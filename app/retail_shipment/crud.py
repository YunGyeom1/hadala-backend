from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict
from uuid import UUID
from datetime import date
from . import models, schemas
from app.retail_contract.models import RetailContract, RetailContractItem

def create_shipment(
    db: Session,
    shipment: schemas.RetailShipmentCreate,
    company_id: UUID
):
    db_shipment = models.RetailShipment(
        company_id=company_id,
        retailer_id=shipment.retailer_id,
        contract_id=shipment.contract_id,
        center_id=shipment.center_id,
        wholesaler_id=shipment.wholesaler_id,
        shipment_date=shipment.shipment_date,
        total_price=shipment.total_price,
        shipment_name=shipment.shipment_name
    )
    db.add(db_shipment)
    db.flush()

    for item in shipment.items:
        db_item = models.RetailShipmentItem(
            shipment_id=db_shipment.id,
            crop_name=item.crop_name,
            quantity_kg=item.quantity_kg,
            unit_price=item.unit_price,
            total_price=item.total_price,
            quality_grade=item.quality_grade
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def get_shipments(
    db: Session,
    company_id: UUID,
    contract_id: Optional[UUID] = None,
    retailer_id: Optional[UUID] = None,
    center_id: Optional[UUID] = None,
    wholesaler_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(models.RetailShipment).filter(models.RetailShipment.company_id == company_id)
    
    if contract_id:
        query = query.filter(models.RetailShipment.contract_id == contract_id)
    if retailer_id:
        query = query.filter(models.RetailShipment.retailer_id == retailer_id)
    if center_id:
        query = query.filter(models.RetailShipment.center_id == center_id)
    if wholesaler_id:
        query = query.filter(models.RetailShipment.wholesaler_id == wholesaler_id)
    if start_date:
        query = query.filter(models.RetailShipment.shipment_date >= start_date)
    if end_date:
        query = query.filter(models.RetailShipment.shipment_date <= end_date)
    
    return query.offset(skip).limit(limit).all()

def get_shipment(db: Session, shipment_id: UUID, company_id: UUID):
    return db.query(models.RetailShipment).filter(
        and_(
            models.RetailShipment.id == shipment_id,
            models.RetailShipment.company_id == company_id
        )
    ).first()

def update_shipment(
    db: Session,
    shipment_id: UUID,
    company_id: UUID,
    shipment_update: schemas.RetailShipmentUpdate
):
    db_shipment = get_shipment(db, shipment_id, company_id)
    if not db_shipment or db_shipment.is_finalized:
        return None

    for field, value in shipment_update.dict(exclude_unset=True).items():
        setattr(db_shipment, field, value)

    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def delete_shipment(
    db: Session,
    shipment_id: UUID,
    company_id: UUID
):
    shipment = get_shipment(db, shipment_id, company_id)
    if not shipment:
        return None
    
    db.delete(shipment)
    db.commit()
    return shipment

def get_shipment_items(
    db: Session,
    shipment_id: UUID,
    company_id: UUID
):
    return db.query(models.RetailShipmentItem).join(
        models.RetailShipment
    ).filter(
        and_(
            models.RetailShipment.id == shipment_id,
            models.RetailShipment.company_id == company_id
        )
    ).all()

def add_shipment_item(
    db: Session,
    shipment_id: UUID,
    company_id: UUID,
    item: schemas.RetailShipmentItemCreate
):
    db_shipment = get_shipment(db, shipment_id, company_id)
    if not db_shipment or db_shipment.is_finalized:
        return None

    db_item = models.RetailShipmentItem(
        shipment_id=shipment_id,
        crop_name=item.crop_name,
        quantity_kg=item.quantity_kg,
        unit_price=item.unit_price,
        total_price=item.total_price,
        quality_grade=item.quality_grade
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_shipment_item(
    db: Session,
    item_id: UUID,
    company_id: UUID,
    item_update: schemas.RetailShipmentItemUpdate
):
    db_item = db.query(models.RetailShipmentItem).join(
        models.RetailShipment
    ).filter(
        and_(
            models.RetailShipmentItem.id == item_id,
            models.RetailShipment.company_id == company_id
        )
    ).first()

    if not db_item or db_item.shipment.is_finalized:
        return None

    for field, value in item_update.dict(exclude_unset=True).items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item

def delete_shipment_item(
    db: Session,
    item_id: UUID,
    company_id: UUID
):
    db_item = db.query(models.RetailShipmentItem).join(
        models.RetailShipment
    ).filter(
        and_(
            models.RetailShipmentItem.id == item_id,
            models.RetailShipment.company_id == company_id
        )
    ).first()

    if not db_item or db_item.shipment.is_finalized:
        return False

    db.delete(db_item)
    db.commit()
    return True

def finalize_shipment(
    db: Session,
    shipment_id: UUID,
    company_id: UUID
):
    db_shipment = get_shipment(db, shipment_id, company_id)
    if not db_shipment or db_shipment.is_finalized:
        return None

    db_shipment.is_finalized = True
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def get_shipment_progress(
    db: Session,
    contract_id: UUID,
    company_id: UUID
):
    # 계약 품목별 총 수량
    contract_items = db.query(
        RetailContractItem.crop_name,
        func.sum(RetailContractItem.quantity_kg).label('total_quantity'),
        RetailContractItem.unit_price
    ).join(
        RetailContract,
        RetailContractItem.contract_id == RetailContract.id
    ).filter(
        and_(
            RetailContractItem.contract_id == contract_id,
            RetailContract.company_id == company_id
        )
    ).group_by(
        RetailContractItem.crop_name,
        RetailContractItem.unit_price
    ).all()

    # 출하된 품목별 수량
    shipped_items = db.query(
        models.RetailShipmentItem.crop_name,
        func.sum(models.RetailShipmentItem.quantity_kg).label('shipped_quantity')
    ).join(
        models.RetailShipment,
        models.RetailShipmentItem.shipment_id == models.RetailShipment.id
    ).filter(
        and_(
            models.RetailShipment.contract_id == contract_id,
            models.RetailShipment.company_id == company_id
        )
    ).group_by(
        models.RetailShipmentItem.crop_name
    ).all()

    # 결과 매핑
    shipped_dict = {item.crop_name: item.shipped_quantity for item in shipped_items}
    
    return [
        {
            "crop_name": item.crop_name,
            "total_quantity": float(item.total_quantity),
            "shipped_quantity": float(shipped_dict.get(item.crop_name, 0)),
            "remaining_quantity": float(item.total_quantity) - float(shipped_dict.get(item.crop_name, 0)),
            "unit_price": float(item.unit_price),
            "total_price": float(item.total_quantity) * float(item.unit_price)
        }
        for item in contract_items
    ] 