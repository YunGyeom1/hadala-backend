from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime

class FarmerCompanyDetailBase(BaseModel):
    address: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    representative: Optional[str] = None
    business_registration_number: Optional[str] = None
    established_year: Optional[int] = None
    
    main_products: Optional[str] = None
    farm_size: Optional[float] = None
    annual_production: Optional[float] = None
    cultivation_method: Optional[str] = None
    certification_info: Optional[str] = None

class FarmerCompanyDetailCreate(FarmerCompanyDetailBase):
    pass

class FarmerCompanyDetailUpdate(FarmerCompanyDetailBase):
    pass

class FarmerCompanyDetailResponse(FarmerCompanyDetailBase):
    company_id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True) 