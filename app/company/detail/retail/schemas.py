from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.company.common.models import CompanyType

class RetailCompanyDetailBase(BaseModel):
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
    
    daily_consumption: Optional[float] = None
    main_products: Optional[str] = None
    preferred_delivery_day: Optional[str] = None

class RetailCompanyDetailCreate(RetailCompanyDetailBase):
    pass

class RetailCompanyDetailUpdate(RetailCompanyDetailBase):
    pass

class RetailCompanyDetailResponse(RetailCompanyDetailBase):
    company_id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 