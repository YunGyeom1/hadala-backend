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

    class Config:
        from_attributes = True

class InventoryBase(BaseModel):
    date: date
    company_id: UUID
    center_id: UUID
    model_config = ConfigDict(from_attributes=True)

class InventoryCreate(InventoryBase):
    items: List[InventoryItemCreate]

class InventoryUpdate(BaseModel):
    date: Optional[date] = None
    items: Optional[List[InventoryItemUpdate]] = None
    model_config = ConfigDict(from_attributes=True)

class Inventory(InventoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    items: List[InventoryItem]

    class Config:
        from_attributes = True

class DailySettlementBase(BaseModel):
    date: date
    company_id: UUID
    center_id: Optional[UUID] = None
    total_wholesale_in_kg: float
    total_retail_out_kg: float
    wholesale_discrepancy_kg: float
    retail_discrepancy_kg: float
    total_inflow_kg: float
    total_outflow_kg: float
    net_flow_kg: float

class DailySettlementCreate(DailySettlementBase):
    pass

class DailySettlementUpdate(BaseModel):
    total_wholesale_in_kg: Optional[float] = None
    total_retail_out_kg: Optional[float] = None
    wholesale_discrepancy_kg: Optional[float] = None
    retail_discrepancy_kg: Optional[float] = None
    total_inflow_kg: Optional[float] = None
    total_outflow_kg: Optional[float] = None
    net_flow_kg: Optional[float] = None

class DailySettlement(DailySettlementBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InventoryOut(InventoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True) 