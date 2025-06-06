from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class FarmerBase(BaseModel):
    name: str
    address: Optional[str] = None
    farm_size_m2: Optional[float] = None
    annual_output_kg: Optional[float] = None
    farm_members: Optional[int] = None

class FarmerCreate(FarmerBase):
    pass

class FarmerUpdate(FarmerBase):
    name: Optional[str] = None

class FarmerInDB(FarmerBase):
    id: UUID4
    user_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FarmerResponse(FarmerInDB):
    pass

class FarmerFilter(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    farm_size_m2_min: Optional[float] = None
    farm_size_m2_max: Optional[float] = None
    annual_output_kg_min: Optional[float] = None
    annual_output_kg_max: Optional[float] = None
    farm_members_min: Optional[int] = None
    farm_members_max: Optional[int] = None