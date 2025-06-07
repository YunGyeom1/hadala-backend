from pydantic import BaseModel, UUID4
from datetime import date, datetime
from typing import List, Optional
from .models import ContractStatus, PaymentStatus

class WholesaleContractItemBase(BaseModel):
    crop_name: str
    quantity_kg: float
    unit_price: float
    quality_required: Optional[str] = None

class WholesaleContractItemCreate(WholesaleContractItemBase):
    pass

class WholesaleContractItemUpdate(BaseModel):
    crop_name: Optional[str] = None
    quantity_kg: Optional[float] = None
    unit_price: Optional[float] = None
    quality_required: Optional[str] = None

class WholesaleContractItem(WholesaleContractItemBase):
    id: UUID4
    contract_id: UUID4
    total_price: float
    created_at: datetime

    class Config:
        from_attributes = True

class WholesaleContractBase(BaseModel):
    center_id: UUID4
    wholesaler_id: UUID4
    farmer_id: UUID4
    company_id: UUID4
    contract_date: date
    note: Optional[str] = None
    shipment_date: date
    total_price: Optional[float] = None

class WholesaleContractCreate(WholesaleContractBase):
    items: List[WholesaleContractItemCreate]

class WholesaleContractUpdate(BaseModel):
    note: Optional[str] = None
    shipment_date: Optional[date] = None
    total_price: Optional[float] = None
    items: Optional[List[WholesaleContractItemCreate]] = None

class WholesaleContract(WholesaleContractBase):
    id: UUID4
    contract_status: ContractStatus
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    items: List[WholesaleContractItem]

    class Config:
        from_attributes = True

class PaymentStatusUpdate(BaseModel):
    payment_status: PaymentStatus 