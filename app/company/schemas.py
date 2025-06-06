from pydantic import BaseModel, UUID4
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

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

class CollectionCenterInCompany(BaseModel):
    id: UUID4
    name: str
    address: Optional[str] = None

    class Config:
        from_attributes = True