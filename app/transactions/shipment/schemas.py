from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, UUID4

from app.transactions.common.models import ProductQuality, ShipmentStatus

class ShipmentItemBase(BaseModel):
    product_name: str
    quality: ProductQuality
    quantity: int
    unit_price: float

class ShipmentItemCreate(ShipmentItemBase):
    pass

class ShipmentItemResponse(ShipmentItemBase):
    id: UUID4
    total_price: float

    class Config:
        from_attributes = True

class ShipmentBase(BaseModel):
    title: str
    contract_id: UUID4
    supplier_person_username: Optional[str] = None
    supplier_company_name: Optional[str] = None
    receiver_person_username: Optional[str] = None
    receiver_company_name: Optional[str] = None
    shipment_datetime: datetime
    departure_center_name: Optional[str] = None
    arrival_center_name: Optional[str] = None
    shipment_status: Optional[ShipmentStatus] = ShipmentStatus.PENDING
    notes: Optional[str] = None

class ShipmentCreate(ShipmentBase):
    items: List[ShipmentItemCreate]

class ShipmentUpdate(ShipmentBase):
    title: Optional[str] = None
    items: Optional[List[ShipmentItemCreate]] = None

class ShipmentResponse(ShipmentBase):
    id: UUID4
    total_price: float
    creator_username: str
    shipment_status: ShipmentStatus
    items: List[ShipmentItemResponse]

    class Config:
        from_attributes = True
