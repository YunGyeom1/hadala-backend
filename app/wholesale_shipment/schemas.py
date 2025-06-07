from pydantic import BaseModel, UUID4
from datetime import date, datetime
from typing import List, Optional

class WholesaleShipmentItemBase(BaseModel):
    crop_name: str
    quantity: float
    unit_price: float
    total_price: float
    quality_grade: Optional[str] = None

class WholesaleShipmentItemCreate(WholesaleShipmentItemBase):
    pass

class WholesaleShipmentItemUpdate(WholesaleShipmentItemBase):
    pass

class WholesaleShipmentItem(WholesaleShipmentItemBase):
    id: UUID4
    shipment_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WholesaleShipmentBase(BaseModel):
    contract_id: UUID4
    farmer_id: UUID4
    center_id: UUID4
    wholesaler_id: UUID4
    shipment_date: date
    total_price: Optional[float] = None

class WholesaleShipmentCreate(WholesaleShipmentBase):
    items: List[WholesaleShipmentItemCreate]

class WholesaleShipmentUpdate(BaseModel):
    shipment_date: Optional[date] = None
    total_price: Optional[float] = None

class WholesaleShipment(WholesaleShipmentBase):
    id: UUID4
    company_id: UUID4
    is_finalized: bool
    created_at: datetime
    updated_at: datetime
    items: List[WholesaleShipmentItem]

    class Config:
        from_attributes = True

class ShipmentProgressItem(BaseModel):
    crop_name: str
    total_quantity: float
    shipped_quantity: float
    remaining_quantity: float
    unit_price: float
    total_price: float

class ContractShipmentProgress(BaseModel):
    contract_id: UUID4
    items: List[ShipmentProgressItem]
    total_shipped_amount: float
    total_remaining_amount: float 