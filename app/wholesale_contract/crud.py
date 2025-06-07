from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
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
    contract_update: schemas.WholesaleContractUpdate
) -> Optional[models.WholesaleContract]:
    """계약 정보를 업데이트합니다."""
    contract = get_contract(db, contract_id)
    if not contract:
        return None
    
    # 결제 상태가 변경되는 경우 로그 생성
    if contract_update.payment_status and contract_update.payment_status != contract.payment_status:
        create_payment_log(
            db=db,
            contract_id=contract_id,
            old_status=contract.payment_status,
            new_status=contract_update.payment_status
        )
    
    update_data = contract_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)
    
    db.commit()
    db.refresh(contract)
    return contract

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

def create_payment_log(
    db: Session,
    contract_id: UUID,
    old_status: models.PaymentStatus,
    new_status: models.PaymentStatus,
    changed_by: Optional[UUID] = None
) -> models.WholesaleContractPaymentLog:
    """결제 상태 변경 로그를 생성합니다."""
    payment_log = models.WholesaleContractPaymentLog(
        contract_id=contract_id,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by
    )
    db.add(payment_log)
    db.commit()
    db.refresh(payment_log)
    return payment_log

def get_contract_payment_logs(
    db: Session,
    contract_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[models.WholesaleContractPaymentLog]:
    """특정 계약의 결제 상태 변경 로그를 조회합니다."""
    return db.query(models.WholesaleContractPaymentLog)\
        .filter(models.WholesaleContractPaymentLog.contract_id == contract_id)\
        .order_by(desc(models.WholesaleContractPaymentLog.changed_at))\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_payment_log(
    db: Session,
    log_id: UUID
) -> Optional[models.WholesaleContractPaymentLog]:
    """특정 결제 상태 변경 로그를 조회합니다."""
    return db.query(models.WholesaleContractPaymentLog)\
        .filter(models.WholesaleContractPaymentLog.id == log_id)\
        .first() 