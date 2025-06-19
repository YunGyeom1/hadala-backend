from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.company.common.crud import get_company_by_name
from app.profile.crud import get_profile_by_username
from app.company.center.crud import get_center_by_name
from app.transactions.contract.models import Contract, ContractItem
from app.transactions.contract.schemas import (
    ContractCreate, ContractUpdate, ContractResponse,
    ContractItemCreate, ContractItemResponse
)
from app.profile.models import Profile
from app.company.common.models import Company

def get_contract(db: Session, contract_id: UUID) -> Optional[Contract]:
    """특정 계약 데이터를 조회합니다."""
    return db.query(Contract).filter(Contract.id == contract_id).first()

def get_contracts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    contract_status: Optional[str] = None,
    is_supplier: Optional[bool] = None
) -> Tuple[List[Contract], int]:
    """계약 데이터 목록을 조회합니다."""
    query = db.query(Contract)
    
    # 필터 조건 적용
    if company_id:
        if is_supplier is not None:
            if is_supplier:
                query = query.filter(Contract.supplier_company_id == company_id)
            else:
                query = query.filter(Contract.receiver_company_id == company_id)
        else:
            query = query.filter(
                or_(
                    Contract.supplier_company_id == company_id,
                    Contract.receiver_company_id == company_id
                )
            )
    if start_date:
        query = query.filter(Contract.contract_datetime >= start_date)
    if end_date:
        query = query.filter(Contract.contract_datetime <= end_date)
    if contract_status:
        query = query.filter(Contract.contract_status == contract_status)
    
    # 전체 개수 조회
    total = query.count()
    
    # 페이지네이션 적용
    contracts = query.offset(skip).limit(limit).all()
    
    return contracts, total

def create_contract(db: Session, contract: ContractCreate, creator_username: str) -> Optional[Contract]:
    """새로운 계약 데이터를 생성합니다."""
    # creator_id 조회
    creator_id = get_profile_by_username(db, creator_username).id
    if not creator_id:
        return None
    
    lookup_map = {
        "supplier_person_username": ("supplier_person_id", get_profile_by_username),
        "supplier_company_name": ("supplier_company_id", get_company_by_name),
        "receiver_person_username": ("receiver_person_id", get_profile_by_username),
        "receiver_company_name": ("receiver_company_id", get_company_by_name),
        "departure_center_name": ("departure_center_id", get_center_by_name),
        "arrival_center_name": ("arrival_center_id", get_center_by_name),
    }

    resolved_ids = {}

    for field_name, (id_name, resolver) in lookup_map.items():
        value = getattr(contract, field_name)
        resolved_ids[id_name] = resolver(db, value).id if value else None

    supplier_person_id = resolved_ids["supplier_person_id"]
    supplier_company_id = resolved_ids["supplier_company_id"]
    receiver_person_id = resolved_ids["receiver_person_id"]
    receiver_company_id = resolved_ids["receiver_company_id"]
    departure_center_id = resolved_ids["departure_center_id"]
    arrival_center_id = resolved_ids["arrival_center_id"]
    
    
    # 계약 데이터 생성
    db_contract = Contract(
        title=contract.title,
        creator_id=creator_id,
        supplier_person_id=supplier_person_id,
        supplier_company_id=supplier_company_id,
        receiver_person_id=receiver_person_id,
        receiver_company_id=receiver_company_id,
        contract_datetime=contract.contract_datetime,
        delivery_datetime=contract.delivery_datetime,
        departure_center_id=departure_center_id,
        arrival_center_id=arrival_center_id,
        payment_due_date=contract.payment_due_date,
        contract_status=contract.contract_status,
        payment_status=contract.payment_status,
        notes=contract.notes
    )
    db.add(db_contract)
    db.flush()
    
    # 계약 아이템 생성
    total_price = 0
    for item in contract.items:
        item_total_price = item.quantity * item.unit_price
        db_item = ContractItem(
            contract_id=db_contract.id,
            product_name=item.product_name,
            quality=item.quality,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item_total_price
        )
        db.add(db_item)
        total_price += item_total_price
    
    # 총 가격 업데이트
    db_contract.total_price = total_price
    db.commit()
    db.refresh(db_contract)
    
    return db_contract

def update_contract(
    db: Session,
    contract_id: UUID,
    contract_update: ContractUpdate
) -> Optional[Contract]:
    """계약 데이터를 업데이트합니다."""
    db_contract = get_contract(db, contract_id)
    if not db_contract:
        return None
    
    # 기본 필드 업데이트
    update_data = contract_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field not in ["items", "supplier_person_username", "supplier_company_name", 
                        "receiver_person_username", "receiver_company_name"]:
            setattr(db_contract, field, value)
    
    pairs = [
        ("supplier_person_username", "supplier_person_id", get_profile_by_username),
        ("supplier_company_name", "supplier_company_id", get_company_by_name),
        ("receiver_person_username", "receiver_person_id", get_profile_by_username),
        ("receiver_company_name", "receiver_company_id", get_company_by_name),
        ("departure_center_name", "departure_center_id", get_center_by_name),
        ("arrival_center_name", "arrival_center_id", get_center_by_name),
    ]

    for input_field, target_field, resolver in pairs:
        val = getattr(contract_update, input_field)
        if val:
            setattr(db_contract, target_field, resolver(db, val).id)
        
    # 아이템 업데이트
    if contract_update.items is not None:
        # 기존 아이템 삭제
        db.query(ContractItem).filter(ContractItem.contract_id == contract_id).delete()
        
        # 새로운 아이템 추가
        total_price = 0
        for item in contract_update.items:
            item_total_price = item.quantity * item.unit_price
            db_item = ContractItem(
                contract_id=db_contract.id,
                product_name=item.product_name,
                quality=item.quality,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item_total_price
            )
            db.add(db_item)
            total_price += item_total_price
        
        # 총 가격 업데이트
        db_contract.total_price = total_price
    
    db.commit()
    db.refresh(db_contract)
    return db_contract

def delete_contract(db: Session, contract_id: UUID) -> bool:
    """계약 데이터를 삭제합니다."""
    db_contract = get_contract(db, contract_id)
    if not db_contract:
        return False
    
    db.delete(db_contract)
    db.commit()
    return True

def get_contract_with_details(db: Session, contract_id: UUID) -> Optional[ContractResponse]:
    """계약 데이터와 관련 상세 정보를 조회합니다."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        return None
    
    # 관계 데이터 로드
    db.refresh(contract)
    
    # 응답 데이터 구성
    return ContractResponse(
        id=contract.id,
        title=contract.title,
        supplier_person_username=contract.supplier_person.username if contract.supplier_person else None,
        supplier_company_name=contract.supplier_company.name if contract.supplier_company else None,
        receiver_person_username=contract.receiver_person.username if contract.receiver_person else None,
        receiver_company_name=contract.receiver_company.name if contract.receiver_company else None,
        departure_center_name=contract.departure_center.name if contract.departure_center else None,
        arrival_center_name=contract.arrival_center.name if contract.arrival_center else None,
        contract_datetime=contract.contract_datetime,
        delivery_datetime=contract.delivery_datetime,
        payment_due_date=contract.payment_due_date,
        contract_status=contract.contract_status,
        payment_status=contract.payment_status,
        notes=contract.notes,
        total_price=contract.total_price,
        creator_username=contract.creator.username,
        items=[
            ContractItemResponse(
                id=item.id,
                product_name=item.product_name,
                quality=item.quality,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price
            ) for item in contract.items
        ]
    ) 