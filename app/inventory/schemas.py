from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

class InventoryItemBase(BaseModel):
    crop_name: str
    quality_grade: str
    quantity: float

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    crop_name: Optional[str] = None
    quality_grade: Optional[str] = None
    quantity: Optional[float] = None

class InventoryItem(InventoryItemBase):
    id: UUID
    inventory_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InventoryCreate(BaseModel):
    date: date
    center_id: UUID
    items: List[InventoryItemCreate]

class InventoryUpdate(BaseModel):
    date: Optional[date] = None
    center_id: Optional[UUID] = None
    items: Optional[List[InventoryItemUpdate]] = None
    model_config = ConfigDict(from_attributes=True)

class InventoryFilter(BaseModel):
    center_id: Optional[UUID] = None
    date: Optional[date] = None
    crop_name: Optional[str] = None
    quality_grade: Optional[str] = None

class Inventory(BaseModel):
    id: UUID
    date: date
    center_id: UUID
    created_at: datetime
    updated_at: datetime
    items: List[InventoryItem]
    model_config = ConfigDict(from_attributes=True)


class DailySettlementBase(BaseModel):
    date: date
    center_id: Optional[UUID] = None
    total_wholesale_in_kg: float
    total_wholesale_in_price: float
    total_retail_out_kg: float
    total_retail_out_price: float
    discrepancy_in_kg: float
    discrepancy_out_kg: float
    total_in_kg: float
    total_out_kg: float

class DailySettlement(DailySettlementBase):
    id: Optional[UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)