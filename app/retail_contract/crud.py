from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from uuid import UUID
from . import models, schemas
from .models import ContractStatus, PaymentStatus

def create_contract(db: Session, contract: schemas.RetailContractCreate) -> models.RetailContract:
    db_contract = models.RetailContract(
        company_id=contract.company_id,
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
            quantity_kg=item.quantity_kg,
            unit_price=item.unit_price,
            total_price=item.quantity_kg * item.unit_price,
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

def get_contract(db: Session, contract_id: UUID) -> Optional[models.RetailContract]:
    return db.query(models.RetailContract).filter(
        and_(
            models.RetailContract.id == contract_id
        )
    ).first()

def update_contract(
    db: Session,
    contract_id: UUID,
    contract_update: schemas.RetailContractUpdate
) -> Optional[models.RetailContract]:
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
    
    update_data = contract_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)
    
    db.commit()
    db.refresh(contract)
    return contract

def delete_contract(db: Session, contract_id: UUID, company_id: UUID) -> bool:
    db_contract = get_contract(db, contract_id)
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
    db_contract = get_contract(db, contract_id)
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
    db_contract = get_contract(db, contract_id)
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

def get_contract_item(db: Session, item_id: UUID, company_id: UUID):
    return db.query(models.RetailContractItem).join(
        models.RetailContract
    ).filter(
        models.RetailContractItem.id == item_id,
        models.RetailContract.company_id == company_id
    ).first()

def update_contract_item(
    db: Session,
    item_id: UUID,
    item_update: schemas.RetailContractItemUpdate,
    company_id: UUID
) -> Optional[models.RetailContractItem]:
    """계약 품목 정보를 업데이트합니다."""
    db_item = get_contract_item(db, item_id, company_id)
    if not db_item:
        return None
    
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
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

def create_payment_log(
    db: Session,
    contract_id: UUID,
    old_status: models.PaymentStatus,
    new_status: models.PaymentStatus,
    changed_by: Optional[UUID] = None
) -> models.RetailContractPaymentLog:
    """결제 상태 변경 로그를 생성합니다."""
    payment_log = models.RetailContractPaymentLog(
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
) -> List[models.RetailContractPaymentLog]:
    """특정 계약의 결제 상태 변경 로그를 조회합니다."""
    return db.query(models.RetailContractPaymentLog)\
        .filter(models.RetailContractPaymentLog.contract_id == contract_id)\
        .order_by(desc(models.RetailContractPaymentLog.changed_at))\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_payment_log(
    db: Session,
    log_id: UUID
) -> Optional[models.RetailContractPaymentLog]:
    """특정 결제 상태 변경 로그를 조회합니다."""
    return db.query(models.RetailContractPaymentLog)\
        .filter(models.RetailContractPaymentLog.id == log_id)\
        .first()

def create_retail_contract_item(
    db: Session,
    contract_id: UUID,
    item: schemas.RetailContractItemCreate
) -> models.RetailContractItem:
    db_item = models.RetailContractItem(
        contract_id=contract_id,
        crop_name=item.crop_name,
        quantity_kg=item.quantity_kg,
        unit_price=item.unit_price,
        total_price=item.quantity_kg * item.unit_price,
        quality_required=item.quality_required
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_retail_contract_item(
    db: Session,
    item_id: UUID,
    item: schemas.RetailContractItemUpdate
) -> Optional[models.RetailContractItem]:
    db_item = db.query(models.RetailContractItem).filter(models.RetailContractItem.id == item_id).first()
    if not db_item:
        return None

    update_data = item.model_dump(exclude_unset=True)
    if "quantity_kg" in update_data and "unit_price" in update_data:
        update_data["total_price"] = update_data["quantity_kg"] * update_data["unit_price"]
    elif "quantity_kg" in update_data:
        update_data["total_price"] = update_data["quantity_kg"] * db_item.unit_price
    elif "unit_price" in update_data:
        update_data["total_price"] = db_item.quantity_kg * update_data["unit_price"]

    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item 