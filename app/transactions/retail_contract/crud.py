from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from uuid import UUID
from typing import List, Optional, Tuple
from datetime import datetime, date
from . import models, schemas
from app.profile.crud import get_profile
from app.transactions.common import schemas as common_schemas
def create_retail_contract(
    db: Session,
    contract_create: schemas.RetailContractCreate,
    creator_id: UUID
) -> models.RetailContract:
    """
    새로운 소매 계약을 생성합니다.
    """
    # 계약 생성
    db_contract = models.RetailContract(
        title=contract_create.title,
        supplier_contractor_id=contract_create.supplier_contractor_id,
        supplier_company_id=contract_create.supplier_company_id,
        receiver_contractor_id=contract_create.receiver_contractor_id,
        receiver_company_id=contract_create.receiver_company_id,
        delivery_datetime=contract_create.delivery_datetime,
        delivery_location=contract_create.delivery_location,
        payment_due_date=contract_create.payment_due_date,
        notes=contract_create.notes,
        creator_id=creator_id
    )
    db.add(db_contract)
    db.flush()  # ID 생성을 위해 flush

    # 아이템 생성
    total_price = 0
    for item in contract_create.items:
        item_total = item.quantity * item.unit_price
        total_price += item_total
        
        db_item = models.RetailContractItem(
            contract_id=db_contract.id,
            product_name=item.product_name,
            quality=item.quality,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item_total
        )
        db.add(db_item)
    
    db_contract.total_price = total_price
    db.commit()
    db.refresh(db_contract)
    return schemas.RetailContractResponse.model_validate(db_contract)

def get_retail_contract(
    db: Session,
    contract_id: UUID
) -> Optional[models.RetailContract]:
    """
    ID로 소매 계약을 조회합니다.
    """
    db_contract = db.query(models.RetailContract).filter(models.RetailContract.id == contract_id).first()
    if not db_contract:
        return None
    return schemas.RetailContractResponse.model_validate(db_contract)

def search_retail_contracts(
    db: Session,
    search_params: schemas.RetailContractSearch,
    current_company_id: UUID
) -> Tuple[List[models.RetailContract], int]:
    """
    소매 계약을 검색합니다.
    """
    query = db.query(models.RetailContract).filter(
        or_(
            models.RetailContract.supplier_company_id == current_company_id,
            models.RetailContract.receiver_company_id == current_company_id
        )
    )

    if search_params.title:
        query = query.filter(models.RetailContract.title.ilike(f"%{search_params.title}%"))
    
    if search_params.start_date:
        query = query.filter(models.RetailContract.contract_date >= search_params.start_date)
    
    if search_params.end_date:
        query = query.filter(models.RetailContract.contract_date <= search_params.end_date)
    
    if search_params.supplier_company_id:
        query = query.filter(models.RetailContract.supplier_company_id == search_params.supplier_company_id)
    
    if search_params.receiver_company_id:
        query = query.filter(models.RetailContract.receiver_company_id == search_params.receiver_company_id)
    
    if search_params.status:
        query = query.filter(models.RetailContract.status == search_params.status)
    
    if search_params.payment_status:
        query = query.filter(models.RetailContract.payment_status == search_params.payment_status)

    # 전체 개수 계산
    total = query.count()

    # 정렬
    if search_params.sort_by:
        sort_column = getattr(models.RetailContract, search_params.sort_by)
        if search_params.sort_desc:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(models.RetailContract.created_at.desc())

    # 페이지네이션
    query = query.offset((search_params.page - 1) * search_params.page_size)
    query = query.limit(search_params.page_size)

    contracts = query.all()
    return [schemas.RetailContractResponse.model_validate(contract) for contract in contracts], total

def get_retail_contract_items(
    db: Session,
    contract_id: UUID
) -> List[models.RetailContractItem]:
    """
    계약의 아이템 리스트를 조회합니다.
    """
    return db.query(models.RetailContractItem).filter(
        models.RetailContractItem.contract_id == contract_id
    ).all()

def get_retail_contract_chain(
    db: Session,
    contract_id: UUID,
    limit: int = 50
) -> List[models.RetailContract]:
    """
    연속 계약 리스트를 조회합니다.
    """
    # 현재 계약 조회
    current_contract = get_retail_contract(db, contract_id)
    if not current_contract:
        return []

    prev_contracts = []
    current = current_contract
    for _ in range((limit - 1) // 2):
        if not current.previous_contract:
            break
        current = current.previous_contract
        prev_contracts.append(current)

    next_contracts = []
    current = current_contract
    for _ in range(limit//2):
        if not current.next_contract_id:
            break
        current = get_retail_contract(db, current.next_contract_id)
        if not current:
            break
        next_contracts.append(current)

    return prev_contracts[::-1] + [current_contract] + next_contracts

def update_retail_contract(
    db: Session,
    contract_id: UUID,
    contract_update: schemas.RetailContractUpdate
) -> Optional[models.RetailContract]:
    """
    소매 계약을 수정합니다.
    """
    db_contract = get_retail_contract(db, contract_id)
    if not db_contract:
        return None

    # 기본 정보 업데이트
    update_data = contract_update.model_dump(exclude_unset=True, exclude={'items'})
    for field, value in update_data.items():
        setattr(db_contract, field, value)

    # 아이템 업데이트
    if contract_update.items is not None:
        # 기존 아이템 삭제
        db.query(models.RetailContractItem).filter(
            models.RetailContractItem.contract_id == contract_id
        ).delete()

        # 새 아이템 추가
        total_price = 0
        for item in contract_update.items:
            item_total = item.quantity * item.unit_price
            total_price += item_total
            
            db_item = models.RetailContractItem(
                contract_id=contract_id,
                product_name=item.product_name,
                quality=item.quality,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item_total
            )
            db.add(db_item)
        
        db_contract.total_price = total_price

    db.commit()
    db.refresh(db_contract)
    return schemas.RetailContractResponse.model_validate(db_contract)

def update_retail_contract_status(
    db: Session,
    contract_id: UUID,
    status: common_schemas.ContractStatusUpdate
) -> Optional[models.RetailContract]:
    """
    계약 상태를 변경합니다.
    """
    db_contract = get_retail_contract(db, contract_id)
    if not db_contract:
        return None

    db_contract.contract_status = status.status
    db.commit()
    db.refresh(db_contract)
    return db_contract

def update_retail_contract_payment_status(
    db: Session,
    contract_id: UUID,
    status: common_schemas.PaymentStatusUpdate
) -> Optional[models.RetailContract]:
    """
    결제 상태를 변경합니다.
    """
    db_contract = get_retail_contract(db, contract_id)
    if not db_contract:
        return None

    db_contract.payment_status = status.status
    db.commit()
    db.refresh(db_contract)
    return db_contract

def delete_retail_contract(
    db: Session,
    contract_id: UUID
) -> bool:
    """
    소매 계약을 삭제합니다.
    """
    db_contract = get_retail_contract(db, contract_id)
    if not db_contract:
        return False

    db.delete(db_contract)
    db.commit()
    return True

def delete_retail_contract_item(
    db: Session,
    contract_id: UUID,
    item_id: UUID
) -> bool:
    """
    계약의 특정 아이템을 삭제합니다.
    """
    db_item = db.query(models.RetailContractItem).filter(
        models.RetailContractItem.contract_id == contract_id,
        models.RetailContractItem.id == item_id
    ).first()
    
    if not db_item:
        return False

    # 계약의 총 금액 업데이트
    db_contract = get_retail_contract(db, contract_id)
    db_contract.total_price -= db_item.total_price

    db.delete(db_item)
    db.commit()
    return True 