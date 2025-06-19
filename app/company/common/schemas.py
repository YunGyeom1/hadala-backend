from pydantic import BaseModel, UUID4
from typing import Optional, List
from .models import CompanyType
from app.profile.models import ProfileRole


class CompanyBase(BaseModel):
    name: str
    type: CompanyType

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(CompanyBase):
    name: Optional[str] = None
    type: Optional[CompanyType] = None
    pass


class CompanyResponse(CompanyBase):
    id: UUID4
    wholesale_company_detail_id: Optional[UUID4] = None

    class Config:
        from_attributes = True

class CompanyOwnerUpdate(BaseModel):
    new_owner_id: UUID4

class CompanyUserAdd(BaseModel):
    profile_id: UUID4
    role: ProfileRole

class CompanyCenterAdd(BaseModel):
    center_id: UUID4

class CompanyCenterRemove(BaseModel):
    center_id: UUID4 