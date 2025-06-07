from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class CenterBase(BaseModel):
    name: str
    address: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class CenterCreate(CenterBase):
    company_id: UUID4

class CenterUpdate(CenterBase):
    pass

class CenterInDB(CenterBase):
    id: UUID4
    company_id: UUID4
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CenterResponse(CenterInDB):
    pass

class CenterFilter(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    company_id: Optional[UUID4] = None

class WholesalerInCenter(BaseModel):
    id: UUID4
    name: str
    role: str
    phone: Optional[str] = None
    joined_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CenterWithWholesalers(CenterResponse):
    wholesalers: List[WholesalerInCenter] = []

class CenterOut(CenterBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True) 