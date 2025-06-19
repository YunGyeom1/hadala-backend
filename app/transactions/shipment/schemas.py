from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, UUID4, ConfigDict

from app.transactions.common.models import ProductQuality, ShipmentStatus

class ShipmentItemBase(BaseModel):
    product_name: str
    quality: ProductQuality
    quantity: int
    unit_price: float
    total_price: float

    # 없는 것: id, shipment_id

class ShipmentItemCreate(ShipmentItemBase):
    shipment_id: UUID4

class ShipmentItemResponse(ShipmentItemBase):
    id: UUID4

    updated_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ShipmentBase(BaseModel):
    title: str
    notes: Optional[str] = None
    contract_id: UUID4

    supplier_person_id: Optional[UUID4] = None
    supplier_company_id: Optional[UUID4] = None
    receiver_person_id: Optional[UUID4] = None
    receiver_company_id: Optional[UUID4] = None
    departure_center_id: Optional[UUID4] = None
    arrival_center_id: Optional[UUID4] = None
    
    shipment_datetime: datetime
    shipment_status: Optional[ShipmentStatus] = ShipmentStatus.PENDING
    
    #없는거: id, creator_id, items

class ShipmentCreate(ShipmentBase):
    items: List[ShipmentItemCreate]

class ShipmentUpdate(ShipmentBase):
    items: Optional[List[ShipmentItemCreate]] = None

class ShipmentResponse(ShipmentBase):
    id: UUID4
    creator_id: UUID4
    items: List[ShipmentItemResponse]

    model_config = ConfigDict(from_attributes=True)

class ShipmentListResponse(BaseModel):
    shipments: List[ShipmentResponse]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)
