from pydantic import BaseModel, EmailStr
from typing import Optional
from pydantic import ConfigDict

class UserCreateOAuth(BaseModel):
    name: str
    email: EmailStr
    oauth_provider: str
    oauth_sub: str

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class OAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut

class OAuthError(BaseModel):
    detail: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(UserOut):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str