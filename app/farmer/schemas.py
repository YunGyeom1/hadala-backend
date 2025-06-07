from pydantic import BaseModel, UUID4, ConfigDict, Field
from typing import Optional
from datetime import datetime


class FarmerBase(BaseModel):
    name: str = Field(..., max_length=100)
    address: Optional[str] = Field(None, max_length=200)
    farm_size_m2: Optional[float] = Field(None, ge=0)
    annual_output_kg: Optional[float] = Field(None, ge=0)
    farm_members: Optional[int] = Field(None, ge=0)


class FarmerCreate(FarmerBase):
    pass


class FarmerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=200)
    farm_size_m2: Optional[float] = Field(None, ge=0)
    annual_output_kg: Optional[float] = Field(None, ge=0)
    farm_members: Optional[int] = Field(None, ge=0)


class FarmerInDB(FarmerBase):
    id: UUID4
    user_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FarmerResponse(FarmerInDB):
    pass

class FarmerFilter(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    farm_size_m2_min: Optional[float] = Field(None, ge=0)
    farm_size_m2_max: Optional[float] = Field(None, ge=0)
    annual_output_kg_min: Optional[float] = Field(None, ge=0)
    annual_output_kg_max: Optional[float] = Field(None, ge=0)
    farm_members_min: Optional[int] = Field(None, ge=0)
    farm_members_max: Optional[int] = Field(None, ge=0)