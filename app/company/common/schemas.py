from pydantic import BaseModel, UUID4
from typing import Optional, List
from .models import CompanyType
from app.profile.models import ProfileRole

class CompanyCreate(BaseModel):
    name: str
    type: CompanyType

class CompanyUpdate(BaseModel):
    name: Optional[str] = None

class CompanyResponse(BaseModel):
    name: str
    type: CompanyType

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