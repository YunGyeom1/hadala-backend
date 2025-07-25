from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.company.common.models import CompanyType

class RetailCompanyDetailBase(BaseModel):
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
    
    daily_consumption: Optional[float] = 0.0
    main_products: Optional[str] = ""
    preferred_delivery_day: Optional[str] = ""

class RetailCompanyDetailCreate(RetailCompanyDetailBase):
    pass

class RetailCompanyDetailUpdate(RetailCompanyDetailBase):
    pass

class RetailCompanyDetailResponse(RetailCompanyDetailBase):
    company_id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True) 