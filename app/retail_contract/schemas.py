from pydantic import BaseModel, UUID4
from datetime import date, datetime
from typing import List, Optional
from .models import ContractStatus, PaymentStatus

class RetailContractItemBase(BaseModel):
    crop_name: str
    quantity_kg: float
    unit_price: float
    quality_required: Optional[str] = None

class RetailContractItemCreate(RetailContractItemBase):
    pass

class RetailContractItemUpdate(BaseModel):
    crop_name: Optional[str] = None
    quantity_kg: Optional[float] = None
    unit_price: Optional[float] = None
    quality_required: Optional[str] = None

class RetailContractItem(RetailContractItemBase):
    id: UUID4
    contract_id: UUID4
    total_price: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RetailContractBase(BaseModel):
    retailer_id: UUID4
    center_id: UUID4
    wholesaler_id: UUID4
    contract_date: date
    note: Optional[str] = None
    shipment_date: date
    total_price: Optional[float] = None

class RetailContractCreate(RetailContractBase):
    items: List[RetailContractItemCreate]

class RetailContractUpdate(BaseModel):
    contract_date: Optional[date] = None
    note: Optional[str] = None
    shipment_date: Optional[date] = None
    total_price: Optional[float] = None

class RetailContract(RetailContractBase):
    id: UUID4
    company_id: UUID4
    contract_status: ContractStatus
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    items: List[RetailContractItem]

    class Config:
        from_attributes = True

class PaymentStatusUpdate(BaseModel):
    payment_status: PaymentStatus 