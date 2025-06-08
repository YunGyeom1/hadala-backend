from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional
from uuid import UUID

class DailySettlementBase(BaseModel):
    date: date
    company_id: UUID
    center_id: UUID
    total_wholesale_in_kg: Optional[float] = 0
    total_wholesale_in_price: Optional[float] = 0
    total_retail_out_kg: Optional[float] = 0
    total_retail_out_price: Optional[float] = 0
    discrepancy_in_kg: Optional[float] = None
    discrepancy_out_kg: Optional[float] = None
    total_in_kg: Optional[float] = None
    total_out_kg: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class DailySettlementCreate(DailySettlementBase):
    pass

class DailySettlementUpdate(BaseModel):
    total_wholesale_in_kg: Optional[float] = None
    total_wholesale_in_price: Optional[float] = None
    total_retail_out_kg: Optional[float] = None
    total_retail_out_price: Optional[float] = None
    discrepancy_in_kg: Optional[float] = None
    discrepancy_out_kg: Optional[float] = None
    total_in_kg: Optional[float] = None
    total_out_kg: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class DailySettlement(DailySettlementBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DailySettlementTotal(BaseModel):
    date: date
    company_id: UUID
    total_wholesale_in_kg: float
    total_wholesale_in_price: float
    total_retail_out_kg: float
    total_retail_out_price: float
    discrepancy_in_kg: Optional[float] = None
    discrepancy_out_kg: Optional[float] = None
    total_in_kg: Optional[float] = None
    total_out_kg: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class DailySettlementCenterTotal(BaseModel):
    date: date
    company_id: UUID
    center_id: UUID
    total_wholesale_in_kg: float
    total_wholesale_in_price: float
    total_retail_out_kg: float
    total_retail_out_price: float
    discrepancy_in_kg: Optional[float] = None
    discrepancy_out_kg: Optional[float] = None
    total_in_kg: Optional[float] = None
    total_out_kg: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class DailyAccountingBase(BaseModel):
    date: date
    company_id: UUID
    total_prepaid: Optional[float] = 0
    total_pre_received: Optional[float] = 0
    total_paid: Optional[float] = 0
    total_received: Optional[float] = 0
    total_pending_payment: Optional[float] = 0
    total_pending_receipt: Optional[float] = 0
    model_config = ConfigDict(from_attributes=True)

class DailyAccountingCreate(DailyAccountingBase):
    pass

class DailyAccountingUpdate(BaseModel):
    total_prepaid: Optional[float] = None
    total_pre_received: Optional[float] = None
    total_paid: Optional[float] = None
    total_received: Optional[float] = None
    total_pending_payment: Optional[float] = None
    total_pending_receipt: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class DailyAccounting(DailyAccountingBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ManagementBase(BaseModel):
    title: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ManagementCreate(ManagementBase):
    pass

class ManagementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ManagementOut(ManagementBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True) 