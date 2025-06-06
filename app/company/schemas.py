from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional, List
from datetime import datetime

class CompanyBase(BaseModel):
    name: str
    description: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(CompanyBase):
    name: Optional[str] = None

class CompanyInDB(CompanyBase):
    id: UUID4
    owner: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CompanyResponse(CompanyInDB):
    pass

class CompanyFilter(BaseModel):
    name: Optional[str] = None
    has_owner: Optional[bool] = None

class WholesalerInCompany(BaseModel):
    id: UUID4
    name: str
    role: Optional[str] = None
    phone: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class CollectionCenterInCompany(BaseModel):
    id: UUID4
    name: str
    address: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)