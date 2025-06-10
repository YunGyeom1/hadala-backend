from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class WholesalerBase(BaseModel):
    user_id: UUID
    name: str = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = None
    company_id: UUID = None
    

class WholesalerCreate(WholesalerBase):
    user_id: Optional[UUID] = None
    model_config = ConfigDict(from_attributes=True)

class WholesalerUpdateProfile(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class WholesalerUpdateCompanyInfo(BaseModel):
    company_id: UUID
    role: str

class WholesalerResponse(WholesalerBase):
    model_config = ConfigDict(from_attributes=True)
