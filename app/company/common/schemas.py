from pydantic import BaseModel, UUID4, ConfigDict, computed_field
from typing import Optional, List
from .models import CompanyType
from app.profile.models import ProfileRole
from app.company.detail.wholesale.schemas import WholesaleCompanyDetailResponse
from app.company.detail.retail.schemas import RetailCompanyDetailResponse
from app.company.detail.farmer.schemas import FarmerCompanyDetailResponse
from app.profile.models import Profile
from app.database.session import get_db

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
    owner_id: UUID4
    wholesale_company_detail: Optional[WholesaleCompanyDetailResponse] = None
    retail_company_detail: Optional[RetailCompanyDetailResponse] = None
    farm_company_detail: Optional[FarmerCompanyDetailResponse] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    @computed_field
    @property
    def owner_name(self) -> Optional[str]:
        """소유자 이름을 반환합니다."""
        if hasattr(self, 'owner_id') and self.owner_id:
            # owner_id로 Profile 조회
            db = next(get_db())
            profile = db.query(Profile).filter(Profile.id == self.owner_id).first()
            if profile:
                return profile.name
        return None

class CompanyOwnerUpdate(BaseModel):
    new_owner_id: UUID4

class CompanyUserAdd(BaseModel):
    profile_id: UUID4
    role: ProfileRole

class CompanyCenterAdd(BaseModel):
    center_id: UUID4

class CompanyCenterRemove(BaseModel):
    center_id: UUID4 

