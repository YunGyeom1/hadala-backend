from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from . import models, schemas
from .models import ContractStatus, PaymentStatus

def create_contract(db: Session, contract: schemas.RetailContractCreate, company_id: UUID) -> models.RetailContract:
    db_contract = models.RetailContract(
        company_id=company_id,
        retailer_id=contract.retailer_id,
        center_id=contract.center_id,
        wholesaler_id=contract.wholesaler_id,
        contract_date=contract.contract_date,
        note=contract.note,
        shipment_date=contract.shipment_date,
        total_price=contract.total_price,
        contract_status=ContractStatus.DRAFT,
        payment_status=PaymentStatus.PENDING
    )
    db.add(db_contract)
    db.flush()

    for item in contract.items:
        db_item = models.RetailContractItem(
            contract_id=db_contract.id,
            crop_name=item.crop_name,
            min_quantity_kg=item.min_quantity_kg,
            max_quantity_kg=item.max_quantity_kg,
            unit_price=item.unit_price,
            quality_required=item.quality_required
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_contract)
    return db_contract

def get_contracts(
    db: Session,
    company_id: UUID,
    status: Optional[ContractStatus] = None,
    retailer_id: Optional[UUID] = None,
    center_id: Optional[UUID] = None,
    wholesaler_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.RetailContract]:
    query = db.query(models.RetailContract).filter(models.RetailContract.company_id == company_id)
    
    if status:
        query = query.filter(models.RetailContract.contract_status == status)
    if retailer_id:
        query = query.filter(models.RetailContract.retailer_id == retailer_id)
    if center_id:
        query = query.filter(models.RetailContract.center_id == center_id)
    if wholesaler_id:
        query = query.filter(models.RetailContract.wholesaler_id == wholesaler_id)
    
    return query.offset(skip).limit(limit).all()

def get_contract(db: Session, contract_id: UUID, company_id: UUID) -> Optional[models.RetailContract]:
    return db.query(models.RetailContract).filter(
        and_(
            models.RetailContract.id == contract_id,
            models.RetailContract.company_id == company_id
        )
    ).first()

def update_contract(
    db: Session,
    contract_id: UUID,
    company_id: UUID,
    contract_update: schemas.RetailContractUpdate
) -> Optional[models.RetailContract]:
    db_contract = get_contract(db, contract_id, company_id)
    if not db_contract:
        return None

    for field, value in contract_update.dict(exclude_unset=True).items():
        setattr(db_contract, field, value)

    db.commit()
    db.refresh(db_contract)
    return db_contract

def delete_contract(db: Session, contract_id: UUID, company_id: UUID) -> bool:
    db_contract = get_contract(db, contract_id, company_id)
    if not db_contract or db_contract.contract_status != ContractStatus.DRAFT:
        return False

    db.delete(db_contract)
    db.commit()
    return True

def update_contract_status(
    db: Session,
    contract_id: UUID,
    company_id: UUID,
    status: ContractStatus
) -> Optional[models.RetailContract]:
    db_contract = get_contract(db, contract_id, company_id)
    if not db_contract:
        return None

    db_contract.contract_status = status
    db.commit()
    db.refresh(db_contract)
    return db_contract

def update_payment_status(
    db: Session,
    contract_id: UUID,
    company_id: UUID,
    payment_status: PaymentStatus
) -> Optional[models.RetailContract]:
    db_contract = get_contract(db, contract_id, company_id)
    if not db_contract:
        return None

    db_contract.payment_status = payment_status
    db.commit()
    db.refresh(db_contract)
    return db_contract

def get_contract_items(
    db: Session,
    contract_id: UUID,
    company_id: UUID
) -> List[models.RetailContractItem]:
    return db.query(models.RetailContractItem).join(
        models.RetailContract
    ).filter(
        and_(
            models.RetailContract.id == contract_id,
            models.RetailContract.company_id == company_id
        )
    ).all()

def update_contract_item(
    db: Session,
    item_id: UUID,
    company_id: UUID,
    item_update: schemas.RetailContractItemUpdate
) -> Optional[models.RetailContractItem]:
    db_item = db.query(models.RetailContractItem).join(
        models.RetailContract
    ).filter(
        and_(
            models.RetailContractItem.id == item_id,
            models.RetailContract.company_id == company_id
        )
    ).first()

    if not db_item:
        return None

    for field, value in item_update.dict(exclude_unset=True).items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item

def delete_contract_item(
    db: Session,
    item_id: UUID,
    company_id: UUID
) -> bool:
    db_item = db.query(models.RetailContractItem).join(
        models.RetailContract
    ).filter(
        and_(
            models.RetailContractItem.id == item_id,
            models.RetailContract.company_id == company_id
        )
    ).first()

    if not db_item:
        return False

    db.delete(db_item)
    db.commit()
    return True 