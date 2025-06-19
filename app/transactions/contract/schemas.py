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

class ContractItemCreate(ContractItemBase):
    pass

class ContractItemResponse(ContractItemBase):
    id: UUID4
    total_price: float

    class Config:
        from_attributes = True

class ContractBase(BaseModel):
    title: str
    supplier_person_username: Optional[str] = None
    supplier_company_name: Optional[str] = None
    receiver_person_username: Optional[str] = None
    receiver_company_name: Optional[str] = None
    departure_center_name: Optional[str] = None
    arrival_center_name: Optional[str] = None
    delivery_datetime: Optional[datetime] = None
    contract_datetime: Optional[datetime] = None
    payment_due_date: Optional[datetime] = None
    contract_status: Optional[ContractStatus] = ContractStatus.DRAFT
    payment_status: Optional[PaymentStatus] = PaymentStatus.PENDING
    notes: Optional[str] = None

class ContractCreate(ContractBase):
    items: List[ContractItemCreate]

class ContractUpdate(ContractBase):
    title: Optional[str] = None
    items: Optional[List[ContractItemCreate]] = None

class ContractResponse(ContractBase):
    id: UUID4
    total_price: float
    creator_username: str
    contract_status: ContractStatus
    items: List[ContractItemResponse]

    class Config:
        from_attributes = True 