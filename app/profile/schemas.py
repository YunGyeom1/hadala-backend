from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.profile.models import ProfileType, ProfileRole

class ProfileBase(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
    # 없는 것: id, user_id, username, role, type, created_at, updated_at

class MyProfileCreate(ProfileBase):
    username: str
    type: ProfileType
    

class MyProfileUpdate(ProfileBase):
    username: Optional[str] = None


class MyProfileResponse(ProfileBase):
    id: UUID
    type: ProfileType
    username: str
    company_id: Optional[UUID] = None
    company_name: Optional[str] = None
    role: Optional[ProfileRole] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExternalProfileCreate(ProfileBase):
    username: str
    type: ProfileType
    company_id: Optional[UUID] = None
    role: Optional[ProfileRole] = None

class ExternalProfileUpdate(ProfileBase):
    username: Optional[str] = None
    type: Optional[ProfileType] = None
    company_id: Optional[UUID] = None
    role: Optional[ProfileRole] = None

class ProfileResponse(ProfileBase):
    id: UUID
    type: ProfileType
    username: str
    company_id: Optional[UUID] = None
    company_name: Optional[str] = None
    role: Optional[ProfileRole] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ProfileRoleUpdate(BaseModel):
    role: ProfileRole

class ProfileCompanyUpdate(BaseModel):
    profile_id: UUID
    company_id: UUID