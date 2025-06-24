from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, UUID4, ConfigDict

from app.transactions.common.models import ProductQuality, ContractStatus, PaymentStatus

class ContractItemBase(BaseModel):
    product_name: str
    quality: ProductQuality
    quantity: int
    unit_price: float
    total_price: float

    # 없는 것: id, contract_id

class ContractItemCreate(ContractItemBase):
    # contract_id will be set by backend when creating items
    pass

class ContractItemResponse(ContractItemBase):
    id: UUID4

    updated_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# 관계 데이터를 위한 스키마들
class ProfileSummary(BaseModel):
    id: UUID4
    username: str
    name: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None

class CompanySummary(BaseModel):
    id: UUID4
    name: str
    business_number: Optional[str] = None
    address: Optional[str] = None

class CenterSummary(BaseModel):
    id: UUID4
    name: str
    address: Optional[str] = None
    region: Optional[str] = None

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
    payment_status: Optional[PaymentStatus] = PaymentStatus.UNPAID
    
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
    items: List[ContractItemResponse]
    
    # 관계 데이터 필드들
    supplier_contractor: Optional[ProfileSummary] = None
    supplier_company: Optional[CompanySummary] = None
    receiver_contractor: Optional[ProfileSummary] = None
    receiver_company: Optional[CompanySummary] = None
    departure_center: Optional[CenterSummary] = None
    arrival_center: Optional[CenterSummary] = None
    creator: Optional[ProfileSummary] = None

    model_config = ConfigDict(from_attributes=True)

# 상태 업데이트를 위한 스키마들
class ContractStatusUpdate(BaseModel):
    contract_status: ContractStatus

class PaymentStatusUpdate(BaseModel):
    payment_status: PaymentStatus 