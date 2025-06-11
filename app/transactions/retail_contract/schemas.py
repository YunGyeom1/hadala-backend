from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Generic
from datetime import datetime, date
from app.transactions.common.models import ContractStatus, PaymentStatus, ProductQuality

# Item Schemas
class RetailContractItemBase(BaseModel):
    product_name: str
    quality: ProductQuality
    quantity: float
    unit_price: float

class RetailContractItemCreate(RetailContractItemBase):
    pass

class RetailContractItemUpdate(RetailContractItemBase):
    pass

class RetailContractItemResponse(RetailContractItemBase):
    id: UUID4
    contract_id: UUID4
    total_price: float

    class Config:
        from_attributes = True

# Contract Schemas
class RetailContractBase(BaseModel):
    title: str
    supplier_contractor_id: Optional[UUID4] = None
    supplier_company_id: Optional[UUID4] = None
    receiver_contractor_id: Optional[UUID4] = None
    receiver_company_id: Optional[UUID4] = None
    delivery_datetime: Optional[datetime] = None
    delivery_location: Optional[str] = None
    payment_due_date: Optional[datetime] = None
    notes: Optional[str] = None

class RetailContractCreate(RetailContractBase):
    items: List[RetailContractItemCreate]

class RetailContractUpdate(RetailContractBase):
    title: Optional[str] = None
    items: Optional[List[RetailContractItemCreate]] = None

class RetailContractResponse(RetailContractBase):
    id: UUID4
    creator_id: UUID4
    total_price: float
    contract_status: ContractStatus
    payment_status: PaymentStatus
    items: List[RetailContractItemResponse]

    class Config:
        from_attributes = True

# Search Schemas
class RetailContractSearch(BaseModel):
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    supplier_company_id: Optional[UUID4] = None
    receiver_company_id: Optional[UUID4] = None
    contract_status: Optional[ContractStatus] = None
    payment_status: Optional[PaymentStatus] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_desc: bool = False


class PaginatedResponse(BaseModel):
    items: List[RetailContractResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: List[RetailContractResponse], total: int, page: int, page_size: int) -> "PaginatedResponse":
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
