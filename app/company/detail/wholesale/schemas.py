from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.company.common.models import CompanyType

class WholesaleCompanyDetailBase(BaseModel):
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
    
    monthly_transaction_volume: Optional[float] = 0.0
    daily_transport_capacity: Optional[float] = 0.0
    main_products: Optional[str] = ""
    has_cold_storage: Optional[bool] = False
    number_of_vehicles: Optional[int] = 0

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

