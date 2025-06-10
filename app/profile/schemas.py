from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.profile.models import ProfileType, ProfileRole

class ProfileBase(BaseModel):
    username: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    company_id: Optional[UUID] = None
    role: Optional[str] = None

class ProfileCreate(ProfileBase):
    type: ProfileType
    user_id: Optional[UUID] = None
    
class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class ProfileResponse(ProfileBase):
    type: ProfileType
    id: UUID

    model_config = ConfigDict(from_attributes=True)

class ProfileRoleUpdate(BaseModel):
    role: ProfileRole