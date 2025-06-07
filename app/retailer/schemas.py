from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class RetailerBase(BaseModel):
    name: str
    address: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class RetailerCreate(RetailerBase):
    pass

class RetailerUpdate(RetailerBase):
    name: Optional[str] = None
    address: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class RetailerOut(RetailerBase):
    id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RetailerFilter(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None 