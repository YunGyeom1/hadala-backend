from pydantic import BaseModel, UUID4, ConfigDict
from datetime import date, datetime
from typing import List, Optional

class RetailShipmentItemBase(BaseModel):
    crop_name: str
    quantity_kg: float
    unit_price: float
    total_price: float
    quality_grade: Optional[str] = None

class RetailShipmentItemCreate(RetailShipmentItemBase):
    pass

class RetailShipmentItemUpdate(RetailShipmentItemBase):
    pass

class RetailShipmentItem(RetailShipmentItemBase):
    id: UUID4
    shipment_id: UUID4
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RetailShipmentBase(BaseModel):
    retailer_id: UUID4
    contract_id: UUID4
    center_id: UUID4
    wholesaler_id: Optional[UUID4] = None
    shipment_date: date
    total_price: Optional[float] = None

class RetailShipmentCreate(RetailShipmentBase):
    items: List[RetailShipmentItemCreate]

class RetailShipmentUpdate(BaseModel):
    shipment_date: Optional[date] = None
    wholesaler_id: Optional[UUID4] = None
    total_price: Optional[float] = None

class RetailShipment(RetailShipmentBase):
    id: UUID4
    company_id: UUID4
    is_finalized: bool
    created_at: datetime
    updated_at: datetime
    items: List[RetailShipmentItem]
    model_config = ConfigDict(from_attributes=True)

class ShipmentProgress(BaseModel):
    crop_name: str
    total_quantity: float
    shipped_quantity: float
    remaining_quantity: float
    unit_price: float
    total_price: float 