from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from uuid import UUID
from datetime import date
from . import models, schemas
from app.wholesale_contract import models as contract_models

def create_shipment(db: Session, shipment: schemas.WholesaleShipmentCreate, company_id: UUID) -> models.WholesaleShipment:
    """새 출고 기록 생성"""
    db_shipment = models.WholesaleShipment(
        contract_id=shipment.contract_id,
        farmer_id=shipment.farmer_id,
        company_id=company_id,
        center_id=shipment.center_id,
        wholesaler_id=shipment.wholesaler_id,
        shipment_date=shipment.shipment_date,
        total_price=shipment.total_price
    )
    db.add(db_shipment)
    db.flush()  # ID 생성을 위해 flush

    # 품목 추가
    for item in shipment.items:
        db_item = models.WholesaleShipmentItem(
            shipment_id=db_shipment.id,
            crop_name=item.crop_name,
            quantity=item.quantity,
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
    skip: int = 0,
    limit: int = 100,
    center_id: Optional[UUID] = None,
    farmer_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[models.WholesaleShipment]:
    """출고 목록 조회"""
    query = db.query(models.WholesaleShipment).filter(
        models.WholesaleShipment.company_id == company_id
    )

    if center_id:
        query = query.filter(models.WholesaleShipment.center_id == center_id)
    if farmer_id:
        query = query.filter(models.WholesaleShipment.farmer_id == farmer_id)
    if start_date:
        query = query.filter(models.WholesaleShipment.shipment_date >= start_date)
    if end_date:
        query = query.filter(models.WholesaleShipment.shipment_date <= end_date)

    return query.offset(skip).limit(limit).all()

def get_shipment(db: Session, shipment_id: UUID, company_id: UUID) -> Optional[models.WholesaleShipment]:
    """특정 출고 조회"""
    return db.query(models.WholesaleShipment).filter(
        and_(
            models.WholesaleShipment.id == shipment_id,
            models.WholesaleShipment.company_id == company_id
        )
    ).first()

def update_shipment(
    db: Session,
    shipment_id: UUID,
    shipment: schemas.WholesaleShipmentUpdate,
    company_id: UUID
) -> Optional[models.WholesaleShipment]:
    """출고 정보 수정"""
    db_shipment = get_shipment(db, shipment_id, company_id)
    if not db_shipment or db_shipment.is_finalized:
        return None

    update_data = shipment.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_shipment, field, value)

    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def delete_shipment(db: Session, shipment_id: UUID, company_id: UUID) -> bool:
    """출고 삭제"""
    db_shipment = get_shipment(db, shipment_id, company_id)
    if not db_shipment or db_shipment.is_finalized:
        return False

    db.delete(db_shipment)
    db.commit()
    return True

def get_shipment_items(
    db: Session,
    shipment_id: UUID,
    company_id: UUID
) -> List[models.WholesaleShipmentItem]:
    """출고 품목 목록 조회"""
    shipment = get_shipment(db, shipment_id, company_id)
    if not shipment:
        return []
    return shipment.items

def update_shipment_item(
    db: Session,
    item_id: UUID,
    item: schemas.WholesaleShipmentItemUpdate,
    company_id: UUID
) -> Optional[models.WholesaleShipmentItem]:
    """출고 품목 수정"""
    db_item = db.query(models.WholesaleShipmentItem).join(
        models.WholesaleShipment
    ).filter(
        and_(
            models.WholesaleShipmentItem.id == item_id,
            models.WholesaleShipment.company_id == company_id,
            ~models.WholesaleShipment.is_finalized
        )
    ).first()

    if not db_item:
        return None

    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item

def delete_shipment_item(db: Session, item_id: UUID, company_id: UUID) -> bool:
    """출고 품목 삭제"""
    db_item = db.query(models.WholesaleShipmentItem).join(
        models.WholesaleShipment
    ).filter(
        and_(
            models.WholesaleShipmentItem.id == item_id,
            models.WholesaleShipment.company_id == company_id,
            ~models.WholesaleShipment.is_finalized
        )
    ).first()

    if not db_item:
        return False

    db.delete(db_item)
    db.commit()
    return True

def get_contract_shipments(
    db: Session,
    contract_id: UUID,
    company_id: UUID
) -> List[models.WholesaleShipment]:
    """계약에 연결된 출고 목록 조회"""
    return db.query(models.WholesaleShipment).filter(
        and_(
            models.WholesaleShipment.contract_id == contract_id,
            models.WholesaleShipment.company_id == company_id
        )
    ).all()

def create_shipment_from_contract(
    db: Session,
    contract_id: UUID,
    shipment: schemas.WholesaleShipmentCreate,
    company_id: UUID
) -> Optional[models.WholesaleShipment]:
    """계약 기준으로 출고 생성"""
    contract = db.query(contract_models.WholesaleContract).filter(
        and_(
            contract_models.WholesaleContract.id == contract_id,
            contract_models.WholesaleContract.company_id == company_id
        )
    ).first()

    if not contract:
        return None

    return create_shipment(db, shipment, company_id)

def get_contract_shipment_progress(
    db: Session,
    contract_id: UUID,
    company_id: UUID
) -> Optional[schemas.ContractShipmentProgress]:
    """계약 품목별 출고 이행 현황 조회"""
    contract = db.query(contract_models.WholesaleContract).filter(
        and_(
            contract_models.WholesaleContract.id == contract_id,
            contract_models.WholesaleContract.company_id == company_id
        )
    ).first()

    if not contract:
        return None

    # 계약 품목별 출고 수량 집계
    shipment_items = db.query(
        contract_models.WholesaleContractItem.crop_name,
        contract_models.WholesaleContractItem.quantity.label('total_quantity'),
        contract_models.WholesaleContractItem.unit_price,
        contract_models.WholesaleContractItem.total_price,
        func.coalesce(func.sum(models.WholesaleShipmentItem.quantity), 0).label('shipped_quantity')
    ).outerjoin(
        models.WholesaleShipment,
        and_(
            models.WholesaleShipment.contract_id == contract_id,
            ~models.WholesaleShipment.is_finalized
        )
    ).outerjoin(
        models.WholesaleShipmentItem,
        models.WholesaleShipmentItem.shipment_id == models.WholesaleShipment.id
    ).filter(
        contract_models.WholesaleContractItem.contract_id == contract_id
    ).group_by(
        contract_models.WholesaleContractItem.crop_name,
        contract_models.WholesaleContractItem.quantity,
        contract_models.WholesaleContractItem.unit_price,
        contract_models.WholesaleContractItem.total_price
    ).all()

    items = []
    total_shipped_amount = 0
    total_remaining_amount = 0

    for item in shipment_items:
        remaining_quantity = item.total_quantity - item.shipped_quantity
        items.append(schemas.ShipmentProgressItem(
            crop_name=item.crop_name,
            total_quantity=item.total_quantity,
            shipped_quantity=item.shipped_quantity,
            remaining_quantity=remaining_quantity,
            unit_price=item.unit_price,
            total_price=item.total_price
        ))
        total_shipped_amount += item.shipped_quantity * item.unit_price
        total_remaining_amount += remaining_quantity * item.unit_price

    return schemas.ContractShipmentProgress(
        contract_id=contract_id,
        items=items,
        total_shipped_amount=total_shipped_amount,
        total_remaining_amount=total_remaining_amount
    )

def finalize_shipment(
    db: Session,
    shipment_id: UUID,
    company_id: UUID
) -> Optional[models.WholesaleShipment]:
    """출고 완료 처리"""
    db_shipment = get_shipment(db, shipment_id, company_id)
    if not db_shipment or db_shipment.is_finalized:
        return None

    db_shipment.is_finalized = True
    db.commit()
    db.refresh(db_shipment)
    return db_shipment 