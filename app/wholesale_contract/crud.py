from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from . import models, schemas
from app.core.auth.utils import get_current_user

def create_contract(db: Session, contract: schemas.WholesaleContractCreate, company_id: UUID) -> models.WholesaleContract:
    db_contract = models.WholesaleContract(
        **contract.dict(exclude={'items'}),
        company_id=company_id
    )
    db.add(db_contract)
    db.flush()  # ID를 얻기 위해 flush

    # 계약 품목 생성
    for item in contract.items:
        db_item = models.WholesaleContractItem(**item.dict(), contract_id=db_contract.id)
        db.add(db_item)

    db.commit()
    db.refresh(db_contract)
    return db_contract

def get_contracts(
    db: Session,
    company_id: UUID,
    skip: int = 0,
    limit: int = 100,
    status: Optional[models.ContractStatus] = None,
    center_id: Optional[UUID] = None,
    wholesaler_id: Optional[UUID] = None,
    farmer_id: Optional[UUID] = None
) -> List[models.WholesaleContract]:
    query = db.query(models.WholesaleContract).filter(models.WholesaleContract.company_id == company_id)
    
    if status:
        query = query.filter(models.WholesaleContract.contract_status == status)
    if center_id:
        query = query.filter(models.WholesaleContract.center_id == center_id)
    if wholesaler_id:
        query = query.filter(models.WholesaleContract.wholesaler_id == wholesaler_id)
    if farmer_id:
        query = query.filter(models.WholesaleContract.farmer_id == farmer_id)
    
    return query.offset(skip).limit(limit).all()

def get_contract(db: Session, contract_id: UUID, company_id: UUID) -> Optional[models.WholesaleContract]:
    return db.query(models.WholesaleContract).filter(
        and_(
            models.WholesaleContract.id == contract_id,
            models.WholesaleContract.company_id == company_id
        )
    ).first()

def update_contract(
    db: Session,
    contract_id: UUID,
    contract: schemas.WholesaleContractUpdate,
    company_id: UUID
) -> Optional[models.WholesaleContract]:
    db_contract = get_contract(db, contract_id, company_id)
    if not db_contract:
        return None
    
    if db_contract.contract_status not in [models.ContractStatus.DRAFT, models.ContractStatus.CONFIRMED]:
        return None

    update_data = contract.dict(exclude_unset=True)
    if 'items' in update_data:
        items = update_data.pop('items')
        # 기존 품목 삭제
        db.query(models.WholesaleContractItem).filter(
            models.WholesaleContractItem.contract_id == contract_id
        ).delete()
        # 새 품목 추가
        for item in items:
            db_item = models.WholesaleContractItem(**item.dict(), contract_id=contract_id)
            db.add(db_item)

    for field, value in update_data.items():
        setattr(db_contract, field, value)

    db.commit()
    db.refresh(db_contract)
    return db_contract

def delete_contract(db: Session, contract_id: UUID, company_id: UUID) -> bool:
    db_contract = get_contract(db, contract_id, company_id)
    if not db_contract or db_contract.contract_status != models.ContractStatus.DRAFT:
        return False
    
    db.delete(db_contract)
    db.commit()
    return True

def update_contract_status(
    db: Session,
    contract_id: UUID,
    new_status: models.ContractStatus,
    company_id: UUID
) -> Optional[models.WholesaleContract]:
    db_contract = get_contract(db, contract_id, company_id)
    if not db_contract:
        return None
    
    db_contract.contract_status = new_status
    db.commit()
    db.refresh(db_contract)
    return db_contract

def update_payment_status(
    db: Session,
    contract_id: UUID,
    new_status: models.PaymentStatus,
    company_id: UUID
) -> Optional[models.WholesaleContract]:
    db_contract = get_contract(db, contract_id, company_id)
    if not db_contract:
        return None
    
    db_contract.payment_status = new_status
    db.commit()
    db.refresh(db_contract)
    return db_contract

def get_contract_items(
    db: Session,
    contract_id: UUID,
    company_id: UUID
) -> List[models.WholesaleContractItem]:
    contract = get_contract(db, contract_id, company_id)
    if not contract:
        return []
    return contract.items

def update_contract_item(
    db: Session,
    item_id: UUID,
    item: schemas.WholesaleContractItemUpdate,
    company_id: UUID
) -> Optional[models.WholesaleContractItem]:
    db_item = db.query(models.WholesaleContractItem).filter(models.WholesaleContractItem.id == item_id).first()
    if not db_item:
        return None
    
    contract = get_contract(db, db_item.contract_id, company_id)
    if not contract or contract.contract_status not in [models.ContractStatus.DRAFT, models.ContractStatus.CONFIRMED]:
        return None

    for field, value in item.dict(exclude_unset=True).items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item

def delete_contract_item(
    db: Session,
    item_id: UUID,
    company_id: UUID
) -> bool:
    db_item = db.query(models.WholesaleContractItem).filter(models.WholesaleContractItem.id == item_id).first()
    if not db_item:
        return False
    
    contract = get_contract(db, db_item.contract_id, company_id)
    if not contract or contract.contract_status not in [models.ContractStatus.DRAFT, models.ContractStatus.CONFIRMED]:
        return False

    db.delete(db_item)
    db.commit()
    return True 