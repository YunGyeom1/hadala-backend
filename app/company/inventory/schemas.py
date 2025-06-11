from pydantic import BaseModel
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
