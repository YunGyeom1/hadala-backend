from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    name: str
    picture_url: Optional[str] = None

class UserCreateOAuth(UserBase):
    oauth_provider: str
    oauth_sub: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    picture_url: Optional[str] = None

class UserOut(UserBase):
    id: UUID
    oauth_sub: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserResponse(UserOut):
    pass

class OAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserOut

class OAuthError(BaseModel):
    detail: str