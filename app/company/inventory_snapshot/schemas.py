from pydantic import BaseModel, UUID4, ConfigDict
from datetime import date
from typing import List
from app.transactions.common.models import ProductQuality
from uuid import UUID

class InventorySnapshotItem(BaseModel):
    product_name: str
    quality: ProductQuality
    quantity: int
    unit_price: float
    total_price: float

class CenterInventorySnapshot(BaseModel):
    center_id: UUID
    center_name: str
    total_quantity: int
    total_price: float
    items: List[InventorySnapshotItem]
    model_config = ConfigDict(from_attributes=True)

class DailyInventorySnapshot(BaseModel):
    snapshot_date: date
    centers: List[CenterInventorySnapshot]

class InventorySnapshotResponse(BaseModel):
    rows: List[DailyInventorySnapshot]

# 수정 요청 스키마
class UpdateInventorySnapshotItemRequest(BaseModel):
    product_name: str
    quality: ProductQuality
    quantity: int
    unit_price: float

class UpdateCenterInventorySnapshotRequest(BaseModel):
    center_id: UUID
    items: List[UpdateInventorySnapshotItemRequest]

class UpdateDailyInventorySnapshotRequest(BaseModel):
    snapshot_date: date
    centers: List[UpdateCenterInventorySnapshotRequest]


class CompanyInventorySnapshot(BaseModel):
    """회사 전체의 일일 재고 스냅샷"""
    snapshot_date: date
    center_snapshots: List[CenterInventorySnapshot]

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
