from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, UUID4

from app.transactions.common.models import ProductQuality, ContractStatus, PaymentStatus

class ContractItemBase(BaseModel):
    product_name: str
    quality: ProductQuality
    quantity: int
    unit_price: float
    total_price: float

    # 없는 것: id, contract_id

class ContractItemCreate(ContractItemBase):
    contract_id: UUID4

class ContractItemResponse(ContractItemBase):
    id: UUID4

    updated_at: datetime
    created_at: datetime
    class Config:
        from_attributes = True

class ContractBase(BaseModel):
    title: str
    notes: Optional[str] = None

    supplier_contractor_id: Optional[UUID4] = None
    supplier_company_id: Optional[UUID4] = None
    receiver_contractor_id: Optional[UUID4] = None
    receiver_company_id: Optional[UUID4] = None
    departure_center_id: Optional[UUID4] = None
    arrival_center_id: Optional[UUID4] = None
    
    delivery_datetime: Optional[datetime] = None
    contract_datetime: Optional[datetime] = None
    payment_due_date: Optional[datetime] = None
    
    contract_status: Optional[ContractStatus] = ContractStatus.DRAFT
    payment_status: Optional[PaymentStatus] = PaymentStatus.PENDING
    
    #없는거: id, total_price, creator_id, next_contract_id, items

class ContractCreate(ContractBase):
    items: List[ContractItemCreate]

class ContractUpdate(ContractBase):
    title: Optional[str] = None
    items: Optional[List[ContractItemCreate]] = None

class ContractResponse(ContractBase):
    id: UUID4
    total_price: float
    creator_id: UUID4
    next_contract_id: Optional[UUID4] = None
    total_price: float
    items: List[ContractItemResponse]

    class Config:
        from_attributes = True 