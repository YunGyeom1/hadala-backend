from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class RetailerBase(BaseModel):
    name: str
    address: Optional[str] = None
    description: Optional[str] = None

class RetailerCreate(RetailerBase):
    pass

class RetailerUpdate(RetailerBase):
    name: Optional[str] = None

class RetailerResponse(RetailerBase):
    id: UUID4
    user_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RetailerFilter(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None 