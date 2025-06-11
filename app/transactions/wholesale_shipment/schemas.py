from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, UUID4

from app.transactions.common.models import ProductQuality, ShipmentStatus, PaymentStatus

class WholesaleShipmentItemBase(BaseModel):
    product_name: str
    quality: ProductQuality
    quantity: int
    unit_price: float
    notes: Optional[str] = None

class WholesaleShipmentItemCreate(WholesaleShipmentItemBase):
    pass

class WholesaleShipmentItemResponse(WholesaleShipmentItemBase):
    id: UUID4
    shipment_id: UUID4
    total_price: float

    class Config:
        from_attributes = True

class WholesaleShipmentBase(BaseModel):
    title: str
    contract_id: UUID4
    supplier_person_id: Optional[UUID4] = None
    supplier_company_id: Optional[UUID4] = None
    receiver_person_id: Optional[UUID4] = None
    receiver_company_id: Optional[UUID4] = None
    shipment_datetime: datetime
    departure_center_id: Optional[UUID4] = None
    arrival_center_id: Optional[UUID4] = None
    payment_due_date: Optional[datetime] = None
    shipment_status: Optional[ShipmentStatus] = ShipmentStatus.PENDING
    payment_status: Optional[PaymentStatus] = PaymentStatus.PENDING
    notes: Optional[str] = None

class WholesaleShipmentCreate(WholesaleShipmentBase):
    items: List[WholesaleShipmentItemCreate]

class WholesaleShipmentUpdate(WholesaleShipmentBase):
    title: Optional[str] = None
    items: Optional[List[WholesaleShipmentItemCreate]] = None

class WholesaleShipmentResponse(WholesaleShipmentBase):
    id: UUID4
    creator_id: UUID4
    total_price: float
    shipment_status: ShipmentStatus
    payment_status: PaymentStatus
    items: List[WholesaleShipmentItemResponse]

    class Config:
        from_attributes = True

class WholesaleShipmentSearch(BaseModel):
    title: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    supplier_company_id: Optional[UUID4] = None
    receiver_company_id: Optional[UUID4] = None
    shipment_status: Optional[ShipmentStatus] = None
    payment_status: Optional[PaymentStatus] = None
    page: int = 1
    page_size: int = 10

class PaginatedResponse(BaseModel):
    items: List[WholesaleShipmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: List[WholesaleShipmentResponse], total: int, page: int, page_size: int) -> "PaginatedResponse":
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        ) 