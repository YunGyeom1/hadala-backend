from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime, date
from app.company.common.models import CompanyType
from app.company.inventory.schemas import CenterInventorySnapshotResponse

class WholesaleCompanyDetailBase(BaseModel):
    address: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    representative: Optional[str] = None
    business_registration_number: Optional[str] = None
    established_year: Optional[int] = None
    
    monthly_transaction_volume: Optional[float] = None
    daily_transport_capacity: Optional[float] = None
    main_products: Optional[str] = None
    has_cold_storage: Optional[bool] = False
    number_of_vehicles: Optional[int] = None

class WholesaleCompanyDetailCreate(WholesaleCompanyDetailBase):
    pass

class WholesaleCompanyDetailUpdate(WholesaleCompanyDetailBase):
    pass

class WholesaleCompanyDetailResponse(WholesaleCompanyDetailBase):

    class Config:
        from_attributes = True

class CompanyInventorySnapshot(BaseModel):
    """회사 전체의 일일 재고 스냅샷"""
    snapshot_date: date
    center_snapshots: List[CenterInventorySnapshotResponse]

    class Config:
        from_attributes = True

class PaginatedCompanyInventorySnapshot(BaseModel):
    """페이지네이션된 회사 재고 스냅샷 응답"""
    items: List[CompanyInventorySnapshot]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: List[CompanyInventorySnapshot],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedCompanyInventorySnapshot":
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
