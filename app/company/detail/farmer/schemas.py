from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime

class FarmerCompanyDetailBase(BaseModel):
    address: Optional[str] = ""
    region: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    representative: Optional[str] = ""
    business_registration_number: Optional[str] = ""
    established_year: Optional[int] = None
    
    main_products: Optional[str] = ""
    farm_size: Optional[float] = 0.0
    annual_production: Optional[float] = 0.0
    cultivation_method: Optional[str] = ""
    certification_info: Optional[str] = ""

class FarmerCompanyDetailCreate(FarmerCompanyDetailBase):
    pass

class FarmerCompanyDetailUpdate(FarmerCompanyDetailBase):
    pass

class FarmerCompanyDetailResponse(FarmerCompanyDetailBase):
    company_id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True) 