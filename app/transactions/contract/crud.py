from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.profile.crud import get_profile_by_username
from app.transactions.contract.models import Contract, ContractItem
from app.transactions.contract.schemas import (
    ContractCreate, ContractUpdate, ContractResponse,
    ContractItemCreate, ContractItemResponse, ProfileSummary, CompanySummary, CenterSummary
)
from app.profile.models import Profile
from app.company.common.models import Company
from app.company.center.models import Center
from app.transactions.common.models import ContractStatus, PaymentStatus

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
        # Enum 값으로 직접 비교
        if isinstance(contract_status, str):
            # 문자열로 전달된 경우 Enum으로 변환
            if contract_status == "draft":
                query = query.filter(Contract.contract_status == ContractStatus.DRAFT)
            elif contract_status == "pending":
                query = query.filter(Contract.contract_status == ContractStatus.PENDING)
            elif contract_status == "approved":
                query = query.filter(Contract.contract_status == ContractStatus.APPROVED)
            elif contract_status == "rejected":
                query = query.filter(Contract.contract_status == ContractStatus.REJECTED)
            elif contract_status == "cancelled":
                query = query.filter(Contract.contract_status == ContractStatus.CANCELLED)
            elif contract_status == "completed":
                query = query.filter(Contract.contract_status == ContractStatus.COMPLETED)
            else:
                query = query.filter(Contract.contract_status == contract_status)
        else:
            # Enum 객체로 전달된 경우 직접 비교
            query = query.filter(Contract.contract_status == contract_status)
    
    # 전체 개수 조회
    total = query.count()
    
    # 페이지네이션 적용
    contracts = query.offset(skip).limit(limit).all()
    
    return contracts, total

def create_contract(db: Session, contract: ContractCreate, creator_username: str) -> Optional[Contract]:
    """새로운 계약 데이터를 생성합니다."""
    # creator_id 조회
    creator_profile = get_profile_by_username(db, creator_username)
    if not creator_profile:
        return None
    
    # 총 가격 미리 계산
    total_price = sum(item.quantity * item.unit_price for item in contract.items)
    
    # 계약 데이터 생성
    db_contract = Contract(
        title=contract.title,
        creator_id=creator_profile.id,
        supplier_contractor_id=contract.supplier_contractor_id,
        supplier_company_id=contract.supplier_company_id,
        receiver_contractor_id=contract.receiver_contractor_id,
        receiver_company_id=contract.receiver_company_id,
        contract_datetime=contract.contract_datetime,
        delivery_datetime=contract.delivery_datetime,
        departure_center_id=contract.departure_center_id,
        arrival_center_id=contract.arrival_center_id,
        payment_due_date=contract.payment_due_date,
        contract_status=contract.contract_status,
        payment_status=contract.payment_status,
        notes=contract.notes,
        total_price=total_price
    )
    db.add(db_contract)
    db.flush()
    
    # 계약 아이템 생성
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
        if field not in ["items"]:
            setattr(db_contract, field, value)
        
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

def update_contract_status(
    db: Session,
    contract_id: UUID,
    contract_status: ContractStatus
) -> Optional[Contract]:
    """계약 상태를 업데이트합니다."""
    db_contract = get_contract(db, contract_id)
    if not db_contract:
        return None
    
    db_contract.contract_status = contract_status
    db.commit()
    db.refresh(db_contract)
    return db_contract

def update_payment_status(
    db: Session,
    contract_id: UUID,
    payment_status: PaymentStatus
) -> Optional[Contract]:
    """결제 상태를 업데이트합니다."""
    db_contract = get_contract(db, contract_id)
    if not db_contract:
        return None
    
    db_contract.payment_status = payment_status
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
    
    # items를 명시적으로 로드
    items = db.query(ContractItem).filter(ContractItem.contract_id == contract_id).all()
    
    # 관계 데이터 조회
    supplier_contractor = None
    if contract.supplier_contractor_id:
        supplier_contractor_profile = db.query(Profile).filter(Profile.id == contract.supplier_contractor_id).first()
        if supplier_contractor_profile:
            supplier_contractor = ProfileSummary(
                id=supplier_contractor_profile.id,
                username=supplier_contractor_profile.username,
                name=supplier_contractor_profile.name,
                email=supplier_contractor_profile.email,
                company_name=supplier_contractor_profile.company_name
            )
    
    supplier_company = None
    if contract.supplier_company_id:
        supplier_company_obj = db.query(Company).filter(Company.id == contract.supplier_company_id).first()
        if supplier_company_obj:
            supplier_company = CompanySummary(
                id=supplier_company_obj.id,
                name=supplier_company_obj.name,
                business_number=None,
                address=None
            )
    
    receiver_contractor = None
    if contract.receiver_contractor_id:
        receiver_contractor_profile = db.query(Profile).filter(Profile.id == contract.receiver_contractor_id).first()
        if receiver_contractor_profile:
            receiver_contractor = ProfileSummary(
                id=receiver_contractor_profile.id,
                username=receiver_contractor_profile.username,
                name=receiver_contractor_profile.name,
                email=receiver_contractor_profile.email,
                company_name=receiver_contractor_profile.company_name
            )
    
    receiver_company = None
    if contract.receiver_company_id:
        receiver_company_obj = db.query(Company).filter(Company.id == contract.receiver_company_id).first()
        if receiver_company_obj:
            receiver_company = CompanySummary(
                id=receiver_company_obj.id,
                name=receiver_company_obj.name,
                business_number=None,
                address=None
            )
    
    departure_center = None
    if contract.departure_center_id:
        departure_center_obj = db.query(Center).filter(Center.id == contract.departure_center_id).first()
        if departure_center_obj:
            departure_center = CenterSummary(
                id=departure_center_obj.id,
                name=departure_center_obj.name,
                address=departure_center_obj.address,
                region=departure_center_obj.region
            )
    
    arrival_center = None
    if contract.arrival_center_id:
        arrival_center_obj = db.query(Center).filter(Center.id == contract.arrival_center_id).first()
        if arrival_center_obj:
            arrival_center = CenterSummary(
                id=arrival_center_obj.id,
                name=arrival_center_obj.name,
                address=arrival_center_obj.address,
                region=arrival_center_obj.region
            )
    
    creator = None
    if contract.creator_id:
        creator_profile = db.query(Profile).filter(Profile.id == contract.creator_id).first()
        if creator_profile:
            creator = ProfileSummary(
                id=creator_profile.id,
                username=creator_profile.username,
                name=creator_profile.name,
                email=creator_profile.email,
                company_name=creator_profile.company_name
            )
    
    # 응답 데이터 구성
    return ContractResponse(
        id=contract.id,
        title=contract.title,
        supplier_contractor_id=contract.supplier_contractor_id,
        supplier_company_id=contract.supplier_company_id,
        receiver_contractor_id=contract.receiver_contractor_id,
        receiver_company_id=contract.receiver_company_id,
        departure_center_id=contract.departure_center_id,
        arrival_center_id=contract.arrival_center_id,
        contract_datetime=contract.contract_datetime,
        delivery_datetime=contract.delivery_datetime,
        payment_due_date=contract.payment_due_date,
        contract_status=contract.contract_status,
        payment_status=contract.payment_status,
        notes=contract.notes,
        total_price=contract.total_price,
        creator_id=contract.creator_id,
        next_contract_id=contract.next_contract_id,
        items=[
            ContractItemResponse(
                id=item.id,
                product_name=item.product_name,
                quality=item.quality,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                created_at=item.created_at,
                updated_at=item.updated_at
            ) for item in items
        ],
        supplier_contractor=supplier_contractor,
        supplier_company=supplier_company,
        receiver_contractor=receiver_contractor,
        receiver_company=receiver_company,
        departure_center=departure_center,
        arrival_center=arrival_center,
        creator=creator
    ) 