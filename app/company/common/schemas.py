from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional, List
from .models import CompanyType
from app.profile.models import ProfileRole
from app.company.detail.wholesale.schemas import WholesaleCompanyDetailResponse
from app.company.detail.retail.schemas import RetailCompanyDetailResponse
from app.company.detail.farmer.schemas import FarmerCompanyDetailResponse

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
    wholesale_company_detail: Optional[WholesaleCompanyDetailResponse] = None
    retail_company_detail: Optional[RetailCompanyDetailResponse] = None
    farm_company_detail: Optional[FarmerCompanyDetailResponse] = None

    model_config = ConfigDict(from_attributes=True)

class CompanyOwnerUpdate(BaseModel):
    new_owner_id: UUID4

class CompanyUserAdd(BaseModel):
    profile_id: UUID4
    role: ProfileRole

class CompanyCenterAdd(BaseModel):
    center_id: UUID4

class CompanyCenterRemove(BaseModel):
    center_id: UUID4 

