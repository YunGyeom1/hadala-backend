from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.company.common.models import CompanyType

class WholesaleCompanyDetailBase(BaseModel):
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
    
    monthly_transaction_volume: Optional[float] = None
    daily_transport_capacity: Optional[float] = None
    main_products: Optional[str] = None
    has_cold_storage: Optional[bool] = False
    number_of_vehicles: Optional[int] = None

class WholesaleCompanyDetailCreate(WholesaleCompanyDetailBase):
    pass

class WholesaleCompanyDetailUpdate(WholesaleCompanyDetailBase):
    pass

class WholesaleCompanyDetailResponse(WholesaleCompanyDetailBase):
    id: UUID4
    company_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

