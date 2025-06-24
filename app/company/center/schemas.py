from pydantic import BaseModel, UUID4, ConfigDict, computed_field
from typing import Optional
from datetime import time

class CenterUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    manager_profile_id: Optional[UUID4] = None
    operating_start: Optional[time] = None
    operating_end: Optional[time] = None
    is_operational: Optional[bool] = None

class CenterResponse(BaseModel):
    id: UUID4
    name: str
    address: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    manager_profile_id: Optional[UUID4] = None
    operating_start: Optional[time] = None
    operating_end: Optional[time] = None
    is_operational: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)
    
    @computed_field
    @property
    def company_name(self) -> Optional[str]:
        """회사 이름을 반환합니다."""
        if hasattr(self, 'company') and self.company:
            return self.company.name
        return None

class CenterCreate(BaseModel):
    name: str
