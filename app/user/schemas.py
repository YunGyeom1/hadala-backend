from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
from uuid import UUID

class UserOut(BaseModel):
    id: UUID
    name: Optional[str] = None
    email: EmailStr
    picture_url: Optional[HttpUrl] = None

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    picture_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class UserUpdate(BaseModel):
    name: Optional[str] = None
    picture_url: Optional[HttpUrl] = None

class UserCreateOAuth(BaseModel):
    id_token: str

class OAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut

class OAuthError(BaseModel):
    detail: str