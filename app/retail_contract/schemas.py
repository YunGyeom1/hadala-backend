from pydantic import BaseModel, UUID4, ConfigDict
from datetime import date, datetime
from typing import List, Optional
from .models import ContractStatus, PaymentStatus
from uuid import UUID

class RetailContractItemBase(BaseModel):
    crop_name: str
    quantity_kg: float
    unit_price: float
    quality_required: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class RetailContractItemCreate(RetailContractItemBase):
    pass

class RetailContractItemUpdate(BaseModel):
    crop_name: Optional[str] = None
    quantity_kg: Optional[float] = None
    unit_price: Optional[float] = None
    quality_required: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class RetailContractItem(RetailContractItemBase):
    id: UUID4
    contract_id: UUID4
    total_price: float
    model_config = ConfigDict(from_attributes=True)

class RetailContractBase(BaseModel):
    retailer_id: UUID4
    center_id: UUID4
    wholesaler_id: UUID4
    contract_date: date
    note: Optional[str] = None
    shipment_date: date
    total_price: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class RetailContractCreate(RetailContractBase):
    items: List[RetailContractItemCreate]

class RetailContractUpdate(BaseModel):
    contract_date: Optional[date] = None
    note: Optional[str] = None
    shipment_date: Optional[date] = None
    total_price: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class RetailContract(RetailContractBase):
    id: UUID4
    company_id: UUID4
    contract_status: ContractStatus
    payment_status: PaymentStatus
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    items: List[RetailContractItem]
    model_config = ConfigDict(from_attributes=True)

class PaymentStatusUpdate(BaseModel):
    payment_status: PaymentStatus 

class RetailContractOut(RetailContractBase):
    id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True) 